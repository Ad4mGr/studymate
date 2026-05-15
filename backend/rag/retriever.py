from . import vector_store
from .embeddings import embed

MAX_CONTEXT_CHARS = 3000


def build_context(query: str, course_ids: list[str] | None = None, user_id: str | None = None, n_results: int = 5) -> tuple[str, list[dict]]:
    query_embedding = embed(query)
    results = vector_store.search(query_embedding, n_results=n_results, course_ids=course_ids, user_id=user_id)

    if not results:
        return "", []

    used = set()
    sources = []

    for r in results:
        cid = r["metadata"]["course_id"]
        if cid not in used:
            used.add(cid)
            sources.append(
                {
                    "course_id": cid,
                    "filename": r["metadata"]["filename"],
                    "score": round(r["score"], 4),
                }
            )

    chars = 0
    context_parts = []
    for r in results:
        content = f"[From: {r['metadata']['filename']}]\n{r['content']}"
        if chars + len(content) > MAX_CONTEXT_CHARS:
            break
        context_parts.append(content)
        chars += len(content)

    context = "\n\n---\n\n".join(context_parts)

    return context, sources


def build_rag_prompt(query: str, course_ids: list[str] | None = None, user_id: str | None = None) -> tuple[str, list[dict]]:
    context, sources = build_context(query, course_ids=course_ids, user_id=user_id)

    if not context:
        return "", sources

    rag_instruction = (
        "You have access to the following course materials. Use them to answer the student's question. "
        "If the materials don't contain the answer, use your own knowledge but mention that the course "
        "materials don't cover this specifically. Cite the source filename when you use it.\n\n"
        f"COURSE MATERIALS:\n{context}"
    )

    return rag_instruction, sources
