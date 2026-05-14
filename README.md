# Studymate — ESPRIT AI Study Agent

AI study assistant for ESPRIT university students (Tunisia).  
Built with **SvelteKit 5** + **FastAPI** + **Groq** + **Turso/SQLite** + **Better Auth**.

## Quick Start

### Prerequisites
- **Node.js** (v20+)
- **Python 3.12+** (with `uv` or `pip`)
- A free **Groq API key** from https://console.groq.com

### 1. Backend (FastAPI)

```bash
cd backend
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Install & run:
uv sync && uv run uvicorn main:app --reload
# or pip install -r requirements.txt && uvicorn main:app --reload
# Runs on http://localhost:8000
```

### 2. Frontend (SvelteKit)

```bash
# From project root:
cp .env.example .env
npm install
npm run dev
# Runs on http://localhost:5173
```

### 3. Open

Visit **http://localhost:5173**, create an account, and start chatting!

## Architecture

```
studymate/
├── backend/
│   └── main.py                        # FastAPI + Groq streaming (port 8000)
├── src/
│   ├── routes/
│   │   ├── +page.svelte               # Main chat UI
│   │   ├── +layout.svelte             # Layout with NavBar
│   │   ├── login/                     # Auth pages
│   │   └── api/conversations/         # REST API for chat history
│   ├── lib/
│   │   ├── components/                # Chat UI components
│   │   └── server/db/                 # Drizzle schema + auth
│   └── hooks.server.ts                # Paraglide + Better Auth
└── drizzle.config.ts                  # Drizzle ORM config (SQLite)
```

## Features

- **Chat** — Streaming AI responses via Groq (Llama 3.1 8B)
- **Auth** — Email/password registration & login (Better Auth)
- **History** — Conversations & messages persisted to SQLite
- **Multi-language** — AI responds in English, French, or Arabic
- **ESPRIT-tuned** — System prompt tailored to Tunisian engineering curriculum

## Phase 2 (planned)

- RAG over ESPRIT course PDFs (ChromaDB)
- Course browser & study planner
- Exam practice generator
