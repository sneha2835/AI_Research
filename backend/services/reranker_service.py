# backend/services/reranker_service.py

from sentence_transformers import CrossEncoder

# 🔥 Load once (important for performance)
_reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


def rerank_chunks(
    query: str,
    chunks,
    top_k: int = 5,
):
    """
    chunks: list of LangChain Document
    Returns: reranked list of Document
    """

    if not chunks:
        return []

    pairs = [
        (query, c.page_content)
        for c in chunks
    ]

    scores = _reranker.predict(pairs)

    ranked = sorted(
        zip(chunks, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    return [doc for doc, _ in ranked[:top_k]]
