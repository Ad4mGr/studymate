import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from groq import Groq
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # SvelteKit dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a study assistant for ESPRIT university students in Tunisia.
ESPRIT (École Supérieure Privée d'Ingénierie et de Technologie) is a leading Tunisian engineering school.

You help students with:
- Programming (Java, Python, C, C++, SQL, PHP, JavaScript, TypeScript)
- Mathematics (algebra, analysis, probability, statistics)
- Computer networks, databases, algorithms, data structures
- Web development, mobile development, software engineering
- Operating systems, computer architecture, cybersecurity

Be concise, clear, and practical. When explaining code, always use examples with proper formatting.

IMPORTANT: Always respond in English unless the student explicitly writes to you in French or Arabic. If they write in French, respond in French. If they write in Arabic, respond in Arabic. Otherwise, default to English."""


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


def stream_response(messages: list[Message]):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *[{"role": m.role, "content": m.content} for m in messages],
        ],
        stream=True,
        max_tokens=1024,
    )
    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


@app.post("/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(stream_response(request.messages), media_type="text/plain")


@app.get("/health")
async def health():
    return {"status": "ok"}
