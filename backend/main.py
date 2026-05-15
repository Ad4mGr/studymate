import json
import os
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from groq import Groq
from pydantic import BaseModel

from rag.processor import process_pdf
from rag.retriever import build_rag_prompt
from rag.vector_store import add_chunks, delete_by_course, get_course_chunk_count

load_dotenv()

app = FastAPI()

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
COURSES_DIR = os.path.join(os.path.dirname(__file__), "courses")
os.makedirs(COURSES_DIR, exist_ok=True)

COURSES_INDEX = os.path.join(os.path.dirname(__file__), "courses_index.json")

SYSTEM_PROMPT = """You are a study assistant for ESPRIT university students in Tunisia.
ESPRIT (École Supérieure Privée d'Ingénierie et de Technologie) is a leading Tunisian engineering school.

You help students with:
- Programming (Java, Python, C, C++, SQL, PHP, JavaScript, TypeScript)
- Mathematics (algebra, analysis, probability, statistics)
- Computer networks, databases, algorithms, data structures
- Web development, mobile development, software engineering
- Operating systems, computer architecture, cybersecurity

Be concise, clear, and practical. When explaining code, always use examples with proper formatting.

IMPORTANT: Always respond in English unless the student explicitly writes to you in French or Arabic."""


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    course_ids: list[str] = []
    user_id: str = ""


def load_courses_index() -> dict:
    if not os.path.exists(COURSES_INDEX):
        return {}
    with open(COURSES_INDEX) as f:
        return json.load(f)


def save_courses_index(index: dict):
    with open(COURSES_INDEX, "w") as f:
        json.dump(index, f, indent=2)


def stream_response(messages: list[Message], extra_system: str = ""):
    system = SYSTEM_PROMPT
    if extra_system:
        system = f"{system}\n\n{extra_system}"

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system},
            *[{"role": m.role, "content": m.content} for m in messages],
        ],
        stream=True,
        max_tokens=2048,
    )
    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


@app.post("/chat")
async def chat(request: ChatRequest):
    if not request.messages:
        return StreamingResponse([], media_type="text/plain")

    last_user_msg = next(
        (m.content for m in reversed(request.messages) if m.role == "user"), ""
    )

    rag_prompt, sources = build_rag_prompt(
        last_user_msg, course_ids=request.course_ids or None, user_id=request.user_id or None
    )

    def generate():
        yield json.dumps({"sources": sources}) + "\n"

        if rag_prompt:
            streaming_messages = [
                *(
                    [{"role": "system", "content": SYSTEM_PROMPT}]
                    if not rag_prompt
                    else []
                ),
                *(m.model_dump() for m in request.messages),
            ]
        else:
            streaming_messages = [m.model_dump() for m in request.messages]

        system = SYSTEM_PROMPT
        if rag_prompt:
            system = f"{system}\n\n{rag_prompt}"

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
                *[{"role": m.role, "content": m.content} for m in request.messages],
            ],
            stream=True,
            max_tokens=2048,
        )
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    return StreamingResponse(generate(), media_type="text/plain")


@app.post("/courses/upload")
async def upload_course(file: UploadFile = File(...), name: str = Form(...), user_id: str = Form(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    course_id = uuid.uuid4().hex[:12]
    ext = os.path.splitext(file.filename)[1]
    saved_path = os.path.join(COURSES_DIR, f"{course_id}{ext}")

    content = await file.read()
    with open(saved_path, "wb") as f:
        f.write(content)

    documents, embeddings, metadatas, ids = process_pdf(
        saved_path, course_id, file.filename
    )

    for m in metadatas:
        m["user_id"] = user_id

    add_chunks(documents, embeddings, metadatas, ids)

    index = load_courses_index()
    index[course_id] = {
        "id": course_id,
        "name": name,
        "filename": file.filename,
        "filepath": saved_path,
        "chunks": len(documents),
        "user_id": user_id,
    }
    save_courses_index(index)

    return {
        "id": course_id,
        "name": name,
        "filename": file.filename,
        "chunks": len(documents),
    }


@app.get("/courses")
async def list_courses(user_id: str):
    index = load_courses_index()
    courses = []
    for cid, data in index.items():
        if data.get("user_id") == user_id:
            courses.append(
                {
                    "id": cid,
                    "name": data.get("name", cid),
                    "filename": data.get("filename", ""),
                    "chunks": data.get("chunks", 0),
                }
            )
    return sorted(courses, key=lambda c: c["name"])


@app.delete("/courses/{course_id}")
async def delete_course(course_id: str, user_id: str):
    index = load_courses_index()
    if course_id not in index:
        raise HTTPException(404, "Course not found")

    if index[course_id].get("user_id") != user_id:
        raise HTTPException(403, "You do not have permission to delete this course")

    filepath = index[course_id].get("filepath", "")
    if filepath and os.path.exists(filepath):
        os.remove(filepath)

    delete_by_course(course_id)

    del index[course_id]
    save_courses_index(index)

    return {"status": "deleted"}


@app.get("/courses/{course_id}/chunks")
async def get_course_chunks(course_id: str):
    count = get_course_chunk_count(course_id)
    return {"course_id": course_id, "chunks": count}


@app.get("/health")
async def health():
    return {"status": "ok"}
