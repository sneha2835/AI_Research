# backend/services/retrieval_service.py

from rank_bm25 import BM25Okapi
from typing import List
import numpy as np

def tokenize(text: str) -> List[str]:
    return text.lower().split()


def bm25_search(query: str, documents: List[str], top_k: int = 20):
    """
    documents: list of chunk texts
    returns: list of (index, score)
    """
    tokenized_docs = [tokenize(doc) for doc in documents]
    bm25 = BM25Okapi(tokenized_docs)

    query_tokens = tokenize(query)
    scores = bm25.get_scores(query_tokens)

    ranked = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True
    )

    return ranked[:top_k]


def normalize(scores: List[float]):
    if not scores:
        return scores
    min_s, max_s = min(scores), max(scores)
    if max_s - min_s == 0:
        return [0.0 for _ in scores]
    return [(s - min_s) / (max_s - min_s) for s in scores]


def hybrid_merge(
    semantic_docs,
    semantic_scores,
    bm25_indices,
    bm25_scores,
    alpha: float = 0.6,
):
    """
    alpha = weight for semantic score
    """
    merged = {}

    sem_norm = normalize(semantic_scores)
    bm_norm = normalize(bm25_scores)

    for doc, score in zip(semantic_docs, sem_norm):
        merged[id(doc)] = {
            "doc": doc,
            "score": alpha * score
        }

    for idx, score in zip(bm25_indices, bm_norm):
        if idx in merged:
            merged[idx]["score"] += (1 - alpha) * score
        else:
            merged[idx] = {
                "doc": semantic_docs[idx],
                "score": (1 - alpha) * score
            }

    return sorted(
        merged.values(),
        key=lambda x: x["score"],
        reverse=True
    )
