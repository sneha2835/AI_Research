import threading
from typing import List
from sentence_transformers import CrossEncoder


# ==================================================
# 🔒 Thread-Safe Lazy Loading
# ==================================================

_lock = threading.Lock()
_reranker = None


def get_reranker():
    """
    Lazily loads the cross-encoder reranker.
    Thread-safe.
    """
    global _reranker

    if _reranker is not None:
        return _reranker

    with _lock:
        if _reranker is None:
            _reranker = CrossEncoder(
                "cross-encoder/ms-marco-MiniLM-L-6-v2",
                max_length=512  # sufficient for chunk reranking
            )

    return _reranker


# ==================================================
# 🧠 Rerank Function
# ==================================================

def rerank(query: str, chunks: List, top_k: int = 5):
    """
    Re-ranks retrieved chunks using a cross-encoder.

    Args:
        query: User question
        chunks: List of LangChain Document objects
        top_k: Number of top results to return

    Returns:
        Top-k most relevant chunks (sorted by relevance)
    """

    if not chunks:
        return []

    model = get_reranker()

    try:
        # Prepare (query, chunk) pairs
        pairs = [(query, c.page_content) for c in chunks]

        # CPU-safe batch size (important for 12GB RAM)
        scores = model.predict(
            pairs,
            batch_size=8,   # safer than 16 on CPU
            show_progress_bar=False
        )

        # Combine chunks with scores
        scored = list(zip(chunks, scores))

        # Sort by score (descending = most relevant first)
        scored.sort(key=lambda x: float(x[1]), reverse=True)

        # Return top_k chunks only
        return [chunk for chunk, _ in scored[:top_k]]

    except Exception as e:
        print("⚠️ Reranker failed:", e)

        # Fail-safe: return first top_k chunks without reranking
        return chunks[:top_k]