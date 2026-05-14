import os
import uuid
import fitz

from .embeddings import embed_batch

CHUNK_SIZE = 600
CHUNK_OVERLAP = 120


def extract_text_from_pdf(filepath: str) -> str:
    doc = fitz.open(filepath)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    return text


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def process_pdf(filepath: str, course_id: str, filename: str) -> tuple[list[str], list[list[float]], list[dict], list[str]]:
    raw_text = extract_text_from_pdf(filepath)
    chunks = chunk_text(raw_text)

    metadatas = []
    ids = []

    for i, chunk in enumerate(chunks):
        metadatas.append(
            {
                "course_id": course_id,
                "filename": filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
        )
        ids.append(f"{course_id}_{uuid.uuid4().hex[:12]}")

    embeddings = embed_batch(chunks)

    return chunks, embeddings, metadatas, ids
