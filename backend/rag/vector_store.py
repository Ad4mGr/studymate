import os
import chromadb
from chromadb.config import Settings

CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma")

_client = None


def get_client():
    global _client
    if _client is None:
        os.makedirs(CHROMA_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_collection():
    return get_client().get_or_create_collection(
        name="esprit_courses",
        metadata={"hnsw:space": "cosine"},
    )


def add_chunks(documents: list[str], embeddings: list[list[float]], metadatas: list[dict], ids: list[str]):
    col = get_collection()
    col.add(documents=documents, embeddings=embeddings, metadatas=metadatas, ids=ids)


def search(query_embedding: list[float], n_results: int = 5, course_ids: list[str] | None = None) -> list[dict]:
    col = get_collection()
    where_filter = None
    if course_ids:
        where_filter = {"course_id": {"$in": course_ids}}
    results = col.query(query_embeddings=[query_embedding], n_results=n_results, where=where_filter)
    output = []
    for i in range(len(results["ids"][0])):
        output.append(
            {
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": results["distances"][0][i] if results["distances"] else 0,
            }
        )
    return output


def delete_by_course(course_id: str):
    col = get_collection()
    col.delete(where={"course_id": course_id})


def get_course_chunk_count(course_id: str) -> int:
    col = get_collection()
    return col.count(where={"course_id": course_id})
