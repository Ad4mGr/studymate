# ESPRIT Study Agent

AI study assistant for ESPRIT students. Built with FastAPI + Groq + SvelteKit.

## Setup

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY in .env (get it free at console.groq.com)
uvicorn main:app --reload
# Runs on http://localhost:8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

## Project Structure

```
esprit-agent/
├── backend/
│   ├── main.py          # FastAPI app + Groq streaming
│   ├── requirements.txt
│   └── .env             # GROQ_API_KEY goes here
└── frontend/
    └── src/
        └── routes/
            └── +page.svelte  # Chat UI
```

## Next Steps

- [ ] Add chat history persistence (Neon DB)
- [ ] Add RAG over ESPRIT course PDFs (LlamaIndex + ChromaDB)
- [ ] Add auth (Better Auth)
- [ ] Deploy (Cloudflare)
