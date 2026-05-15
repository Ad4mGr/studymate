import json
import os
import uuid
import hashlib
from time import time

import jwt
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
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

rate_limit_store: dict[str, list[float]] = {}

cache_store: dict[str, dict] = {}
CACHE_TTL = 300  # 5 minutes


def get_cache_key(prefix: str, user_id: str, **kwargs) -> str:
    parts = [prefix, user_id] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
    return hashlib.md5("|".join(parts).encode()).hexdigest()


def get_cached(key: str) -> dict | None:
    entry = cache_store.get(key)
    if entry and time() - entry["time"] < CACHE_TTL:
        return entry["data"]
    if entry:
        del cache_store[key]
    return None


def set_cache(key: str, data):
    cache_store[key] = {"data": data, "time": time()}


def invalidate_cache(prefix: str, user_id: str):
    keys_to_delete = [k for k in cache_store if k.startswith(f"{prefix}:{user_id}")]
    for k in keys_to_delete:
        del cache_store[k]


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

    cache_key = get_cache_key("chat", user_id, query=last_user_msg[:100], courses=",".join(sorted(request.course_ids)))
    cached = get_cached(cache_key)
    if cached and not request.course_ids:
        def generate_cached():
            yield json.dumps({"sources": cached["sources"]}) + "\n"
            yield cached["response"]

        return StreamingResponse(generate_cached(), media_type="text/plain")

    rag_prompt, sources = build_rag_prompt(
        last_user_msg, course_ids=request.course_ids or None, user_id=user_id
    )

    def generate():
        full_response = ""
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
                full_response += delta
                yield delta

        if not request.course_ids:
            set_cache(cache_key, {"sources": sources, "response": full_response})

    return StreamingResponse(generate(), media_type="text/plain")


@app.post("/courses/upload")
async def upload_course(
    file: UploadFile = File(...),
    name: str = Form(...),
    tags: str = Form(""),
    req: Request = None
):
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

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    for m in metadatas:
        m["user_id"] = user_id
        m["tags"] = ",".join(tag_list)

    add_chunks(documents, embeddings, metadatas, ids)

    index = load_courses_index()
    index[course_id] = {
        "id": course_id,
        "name": name,
        "filename": file.filename,
        "filepath": saved_path,
        "chunks": len(documents),
        "user_id": user_id,
        "tags": tag_list,
        "created_at": time(),
    }
    save_courses_index(index)

    invalidate_cache("courses", user_id)

    return {
        "id": course_id,
        "name": name,
        "filename": file.filename,
        "chunks": len(documents),
        "tags": tag_list,
    }


@app.get("/courses")
async def list_courses(
    req: Request,
    tag: str | None = Query(None),
    search: str | None = Query(None)
):
    user_id = verify_jwt(req)

    cache_key = get_cache_key("courses", user_id, tag=tag or "", search=search or "")
    cached = get_cached(cache_key)
    if cached:
        return cached

    index = load_courses_index()
    courses = []
    for cid, data in index.items():
        if data.get("user_id") != user_id:
            continue

        if tag and tag not in data.get("tags", []):
            continue

        if search and search.lower() not in data.get("name", "").lower() and search.lower() not in data.get("filename", "").lower():
            continue

        courses.append(
            {
                "id": cid,
                "name": data.get("name", cid),
                "filename": data.get("filename", ""),
                "chunks": data.get("chunks", 0),
                "tags": data.get("tags", []),
                "created_at": data.get("created_at", 0),
            }
        )

    result = sorted(courses, key=lambda c: c["name"])
    set_cache(cache_key, result)
    return result


@app.get("/courses/{course_id}/preview")
async def preview_course(course_id: str, req: Request):
    user_id = verify_jwt(req)

    index = load_courses_index()
    if course_id not in index:
        raise HTTPException(404, "Course not found")

    if index[course_id].get("user_id") != user_id:
        raise HTTPException(403, "You do not have permission to view this course")

    course_data = index[course_id]
    preview_chunks = []

    try:
        from rag.vector_store import get_collection
        col = get_collection()
        results = col.get(
            where={"course_id": course_id},
            limit=5,
            include=["documents", "metadatas"]
        )
        if results and results["documents"]:
            for i in range(min(5, len(results["documents"]))):
                preview_chunks.append({
                    "content": results["documents"][i][:500],
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
                })
    except Exception:
        pass

    return {
        "id": course_id,
        "name": course_data.get("name", ""),
        "filename": course_data.get("filename", ""),
        "chunks": course_data.get("chunks", 0),
        "tags": course_data.get("tags", []),
        "preview": preview_chunks,
    }


@app.get("/courses/{course_id}/export")
async def export_course(course_id: str, req: Request):
    user_id = verify_jwt(req)

    index = load_courses_index()
    if course_id not in index:
        raise HTTPException(404, "Course not found")

    if index[course_id].get("user_id") != user_id:
        raise HTTPException(403, "You do not have permission to export this course")

    course_data = index[course_id]
    return {
        "id": course_id,
        "name": course_data.get("name", ""),
        "filename": course_data.get("filename", ""),
        "tags": course_data.get("tags", []),
        "chunks": course_data.get("chunks", 0),
    }


@app.post("/courses/import")
async def import_course(req: Request):
    user_id = verify_jwt(req)

    try:
        body = await req.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body")

    course_id = body.get("id")
    name = body.get("name")
    tags = body.get("tags", [])

    if not course_id or not name:
        raise HTTPException(400, "Missing required fields: id, name")

    index = load_courses_index()

    if course_id in index and index[course_id].get("user_id") != user_id:
        raise HTTPException(403, "This course already exists and belongs to another user")

    index[course_id] = {
        "id": course_id,
        "name": name,
        "filename": body.get("filename", ""),
        "filepath": os.path.join(COURSES_DIR, f"{course_id}.pdf"),
        "chunks": body.get("chunks", 0),
        "user_id": user_id,
        "tags": tags,
        "created_at": time(),
    }
    save_courses_index(index)

    invalidate_cache("courses", user_id)

    return {
        "id": course_id,
        "name": name,
        "tags": tags,
        "chunks": body.get("chunks", 0),
    }


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

    invalidate_cache("courses", user_id)

    return {"status": "deleted"}


@app.patch("/courses/{course_id}")
async def update_course(course_id: str, req: Request):
    user_id = verify_jwt(req)

    index = load_courses_index()
    if course_id not in index:
        raise HTTPException(404, "Course not found")

    if index[course_id].get("user_id") != user_id:
        raise HTTPException(403, "You do not have permission to update this course")

    try:
        body = await req.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body")

    if "name" in body:
        index[course_id]["name"] = body["name"]
    if "tags" in body:
        index[course_id]["tags"] = body["tags"]

    save_courses_index(index)
    invalidate_cache("courses", user_id)

    return {
        "id": course_id,
        "name": index[course_id]["name"],
        "tags": index[course_id].get("tags", []),
    }


@app.get("/courses/{course_id}/chunks")
async def get_course_chunks(course_id: str, req: Request):
    verify_jwt(req)
    count = get_course_chunk_count(course_id)
    return {"course_id": course_id, "chunks": count}


@app.get("/courses/tags")
async def get_course_tags(req: Request):
    user_id = verify_jwt(req)

    cache_key = get_cache_key("tags", user_id)
    cached = get_cached(cache_key)
    if cached:
        return cached

    index = load_courses_index()
    all_tags = set()
    for data in index.values():
        if data.get("user_id") == user_id:
            all_tags.update(data.get("tags", []))

    result = sorted(all_tags)
    set_cache(cache_key, result)
    return result


@app.get("/courses/{course_id}/flashcards")
async def generate_flashcards(course_id: str, req: Request):
    user_id = verify_jwt(req)

    index = load_courses_index()
    if course_id not in index:
        raise HTTPException(404, "Course not found")

    if index[course_id].get("user_id") != user_id:
        raise HTTPException(403, "You do not have permission to access this course")

    try:
        from rag.vector_store import get_collection
        col = get_collection()
        results = col.get(
            where={"course_id": course_id},
            limit=10,
            include=["documents"]
        )

        if not results or not results["documents"] or len(results["documents"]) < 3:
            raise HTTPException(400, "Not enough content in this course to generate flashcards. Upload more material.")

        context = "\n\n---\n\n".join(results["documents"][:10])

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": """You are a tutor. Extract exactly 10 key concepts from the provided text and return them as a JSON array of objects with 'front' (question) and 'back' (answer) properties.

Rules:
- Return ONLY valid JSON, no markdown, no explanation
- Each object must have exactly two fields: "front" and "back"
- "front" should be a question or term
- "back" should be the answer or definition
- Keep answers concise (1-3 sentences max)
- Return exactly 10 flashcards"""},
                {"role": "user", "content": f"Generate flashcards from this course material:\n\n{context}"}
            ],
            temperature=0.3,
            max_tokens=2048,
        )

        content = response.choices[0].message.content

        text = content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        if text.startswith("json"):
            text = text[4:].strip()

        flashcards = json.loads(text)

        if not isinstance(flashcards, list) or len(flashcards) == 0:
            raise HTTPException(500, "Failed to generate valid flashcards")

        return {"flashcards": flashcards[:10], "course_id": course_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to generate flashcards: {str(e)}")


QUIZ_SESSIONS: dict[str, dict] = {}


@app.post("/courses/{course_id}/quiz")
async def start_quiz(course_id: str, req: Request):
    user_id = verify_jwt(req)

    index = load_courses_index()
    if course_id not in index:
        raise HTTPException(404, "Course not found")

    if index[course_id].get("user_id") != user_id:
        raise HTTPException(403, "You do not have permission to access this course")

    try:
        from rag.vector_store import get_collection
        col = get_collection()
        results = col.get(
            where={"course_id": course_id},
            limit=15,
            include=["documents"]
        )

        if not results or not results["documents"] or len(results["documents"]) < 3:
            raise HTTPException(400, "Not enough content in this course to generate a quiz.")

        context = "\n\n---\n\n".join(results["documents"][:15])

        session_id = uuid.uuid4().hex[:16]
        QUIZ_SESSIONS[session_id] = {
            "user_id": user_id,
            "course_id": course_id,
            "context": context,
            "course_name": index[course_id].get("name", ""),
            "score": 0,
            "total": 0,
            "current_question": 0,
            "max_questions": 5,
            "answers": [],
            "history": [],
        }

        first_question = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": f"""You are a Quiz Master for the course "{index[course_id].get('name', '')}".

Rules:
1. Ask ONE question at a time based on the course material
2. Questions should test understanding, not just recall
3. Mix question types: definitions, concepts, applications
4. After the user answers, evaluate as Correct, Incorrect, or Partial
5. Give a brief explanation for the correct answer
6. Then ask the next question
7. After 5 questions, output a final summary in this JSON format:
{{"quiz_complete": true, "score": X, "total": 5, "feedback": "Review concept X..."}}

Start with question 1 now. Ask only the question, nothing else."""},
                {"role": "user", "content": f"Course material:\n\n{context}\n\nAsk question 1."}
            ],
            temperature=0.7,
            max_tokens=512,
        )

        question = first_question.choices[0].message.content.strip()
        QUIZ_SESSIONS[session_id]["history"].append({"role": "assistant", "content": question})
        QUIZ_SESSIONS[session_id]["current_question"] = 1

        return {
            "session_id": session_id,
            "question": question,
            "question_number": 1,
            "total_questions": 5,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to start quiz: {str(e)}")


@app.post("/courses/{course_id}/quiz/{session_id}/answer")
async def answer_quiz(course_id: str, session_id: str, req: Request):
    user_id = verify_jwt(req)

    if session_id not in QUIZ_SESSIONS:
        raise HTTPException(404, "Quiz session not found or expired")

    session = QUIZ_SESSIONS[session_id]
    if session["user_id"] != user_id:
        raise HTTPException(403, "This quiz session belongs to another user")

    if session["course_id"] != course_id:
        raise HTTPException(400, "Course ID mismatch")

    try:
        body = await req.json()
        user_answer = body.get("answer", "")

        if not user_answer.strip():
            raise HTTPException(400, "Answer cannot be empty")

        session["history"].append({"role": "user", "content": user_answer})

        is_last = session["current_question"] >= session["max_questions"]

        system_prompt = f"""You are evaluating a student's answer to a quiz question.

Evaluate the answer as:
- "correct" if the answer is accurate
- "incorrect" if the answer is wrong
- "partial" if the answer has some correct elements but is incomplete

Provide:
1. evaluation: "correct", "incorrect", or "partial"
2. explanation: a brief explanation of the correct answer (2-3 sentences)
3. next_question: the next quiz question (ONLY if this is not the last question)

If this is question {session["max_questions"]} of {session["max_questions"]}, output a final summary in JSON:
{{"quiz_complete": true, "score": X, "total": {session["max_questions"]}, "feedback": "Review concept X..."}}

Current question: {session["current_question"]}/{session["max_questions"]}"""

        if is_last:
            system_prompt += "\n\nThis is the LAST question. After evaluating, output the quiz_complete JSON summary."
        else:
            system_prompt += f"\n\nAfter evaluating, ask question {session['current_question'] + 1}."

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                *session["history"],
            ],
            temperature=0.3,
            max_tokens=1024,
        )

        result = response.choices[0].message.content.strip()

        evaluation = "partial"
        explanation = result
        next_question = None
        quiz_complete = None

        if "quiz_complete" in result.lower():
            import re
            json_match = re.search(r'\{[^}]*"quiz_complete"[^}]*\}', result, re.DOTALL)
            if json_match:
                try:
                    quiz_complete = json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            eval_match = re.search(r'(?:evaluation|correct|incorrect|partial)[:\s]*(correct|incorrect|partial)', result, re.IGNORECASE)
            if eval_match:
                evaluation = eval_match.group(1).lower()

            exp_match = re.search(r'(?:explanation)[:\s]*(.*?)(?:\n\n|\nnext_question|$)', result, re.IGNORECASE | re.DOTALL)
            if exp_match:
                explanation = exp_match.group(1).strip()
        else:
            eval_match = re.search(r'(?:evaluation)[:\s]*(correct|incorrect|partial)', result, re.IGNORECASE)
            if eval_match:
                evaluation = eval_match.group(1).lower()

            exp_match = re.search(r'(?:explanation)[:\s]*(.*?)(?:\n\n|\nnext_question|$)', result, re.IGNORECASE | re.DOTALL)
            if exp_match:
                explanation = exp_match.group(1).strip()

            q_match = re.search(r'(?:next_question)[:\s]*(.*?)(?:\n\n|$)', result, re.IGNORECASE | re.DOTALL)
            if q_match:
                next_question = q_match.group(1).strip()
            else:
                parts = result.split("\n\n")
                if len(parts) > 1:
                    next_question = parts[-1].strip()

        if evaluation == "correct":
            session["score"] += 1
        session["total"] += 1

        session["answers"].append({
            "question_number": session["current_question"],
            "evaluation": evaluation,
            "explanation": explanation,
        })

        if next_question:
            session["history"].append({"role": "assistant", "content": next_question})
            session["current_question"] += 1

        return {
            "session_id": session_id,
            "evaluation": evaluation,
            "explanation": explanation,
            "next_question": next_question,
            "score": session["score"],
            "total": session["total"],
            "quiz_complete": quiz_complete is not None,
            "summary": quiz_complete,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to process answer: {str(e)}")


@app.get("/health")
async def health():
    return {"status": "ok"}
