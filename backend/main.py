import json
import os
import uuid
from functools import wraps
from time import time

import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
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

JWT_SECRET = os.environ.get("BACKEND_JWT_SECRET", os.environ.get("BETTER_AUTH_SECRET", "fallback-secret-change-in-production"))

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = {
    "/chat": 10,
    "/courses/upload": 5,
    "/courses": 30,
}

rate_limit_store: dict[str, list[float]] = {}


def verify_jwt(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid authorization header")

    token = auth_header[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(401, "Invalid token: missing user_id")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


def check_rate_limit(endpoint: str, client_ip: str):
    key = f"{endpoint}:{client_ip}"
    now = time()
    window_start = now - RATE_LIMIT_WINDOW

    if key not in rate_limit_store:
        rate_limit_store[key] = []

    rate_limit_store[key] = [t for t in rate_limit_store[key] if t > window_start]

    if len(rate_limit_store[key]) >= RATE_LIMIT_MAX_REQUESTS.get(endpoint, 30):
        raise HTTPException(429, "Rate limit exceeded. Try again later.")

    rate_limit_store[key].append(now)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"

    path = request.url.path
    if path.startswith("/courses"):
        if request.method == "POST":
            endpoint = "/courses/upload"
        elif request.method == "GET" and path.endswith("/chunks"):
            endpoint = "/courses"
        else:
            endpoint = "/courses"
    elif path == "/chat":
        endpoint = "/chat"
    else:
        return await call_next(request)

    try:
        check_rate_limit(endpoint, client_ip)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

    return await call_next(request)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    course_ids: list[str] = []


def load_courses_index() -> dict:
    if not os.path.exists(COURSES_INDEX):
        return {}
    with open(COURSES_INDEX) as f:
        return json.load(f)


def save_courses_index(index: dict):
    with open(COURSES_INDEX, "w") as f:
        json.dump(index, f, indent=2)


@app.post("/chat")
async def chat(request: ChatRequest, req: Request):
    user_id = verify_jwt(req)

    if not request.messages:
        return StreamingResponse([], media_type="text/plain")

    last_user_msg = next(
        (m.content for m in reversed(request.messages) if m.role == "user"), ""
    )

    rag_prompt, sources = build_rag_prompt(
        last_user_msg, course_ids=request.course_ids or None, user_id=user_id
    )

    def generate():
        yield json.dumps({"sources": sources}) + "\n"

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
async def upload_course(file: UploadFile = File(...), name: str = Form(...), req: Request = None):
    user_id = verify_jwt(req)

    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(400, f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB")

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
async def list_courses(req: Request):
    user_id = verify_jwt(req)

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
async def delete_course(course_id: str, req: Request):
    user_id = verify_jwt(req)

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
async def get_course_chunks(course_id: str, req: Request):
    verify_jwt(req)
    count = get_course_chunk_count(course_id)
    return {"course_id": course_id, "chunks": count}


@app.get("/health")
async def health():
    return {"status": "ok"}
