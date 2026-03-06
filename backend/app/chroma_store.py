# backend/app/chroma_store.py

from dotenv import load_dotenv
load_dotenv()

import os
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_chroma import Chroma
from app.config import settings


# --------------------------------------------------
# Persistent Chroma directory
# --------------------------------------------------

PERSIST_DIR = settings.CHROMA_PERSIST_DIR
os.makedirs(PERSIST_DIR, exist_ok=True)

print("🔥 Chroma persist directory:", PERSIST_DIR)


# --------------------------------------------------
# Safe SentenceTransformer Wrapper
# --------------------------------------------------

class SentenceTransformerEmbedder:
    """
    Safe wrapper for SentenceTransformer.
    Prevents tokenizer crashes from bad inputs.
    """

    def __init__(self, model):
        self.model = model

    def embed_documents(self, texts):

        safe_texts = []

        for t in texts:
            if t is None:
                continue

            if not isinstance(t, str):
                t = str(t)

            cleaned = t.strip()

            if not cleaned:
                continue

            safe_texts.append(f"passage: {cleaned}")

        if not safe_texts:
            return []

        embeddings = self.model.encode(
            safe_texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embeddings.tolist()

    def embed_query(self, text):

        if text is None:
            text = ""

        if not isinstance(text, str):
            text = str(text)

        cleaned = text.strip()

        if not cleaned:
            cleaned = "empty"

        embedding = self.model.encode(
            [f"query: {cleaned}"],
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embedding[0].tolist()


# --------------------------------------------------
# Initialize Embedding Model
# --------------------------------------------------

_embedding_model = SentenceTransformer(settings.SENTENCE_EMBED_MODEL)
_embedder = SentenceTransformerEmbedder(_embedding_model)


# --------------------------------------------------
# Persistent Chroma Client
# --------------------------------------------------

client = chromadb.PersistentClient(path=PERSIST_DIR)


# --------------------------------------------------
# 📚 Research Papers (arXiv abstracts)
# --------------------------------------------------

research_vector_store = Chroma(
    collection_name="research_papers",
    client=client,
    embedding_function=_embedder,
)


def add_research_abstracts(abstracts, metadatas, ids):

    if not settings.ENABLE_CHROMA or not abstracts:
        return

    safe_abstracts = []

    for a in abstracts:
        if not a:
            continue
        if not isinstance(a, str):
            a = str(a)
        cleaned = a.strip()
        if cleaned:
            safe_abstracts.append(cleaned)

    if not safe_abstracts:
        return

    research_vector_store.add_texts(
        texts=safe_abstracts,
        metadatas=metadatas,
        ids=ids,
    )


def search_research_papers(query, n_results=5):

    return research_vector_store.similarity_search(
        query=str(query),
        k=min(n_results, 15),
    )


# --------------------------------------------------
# 📄 PDF Chunks (uploads + arXiv)
# --------------------------------------------------

pdf_vector_store = Chroma(
    collection_name="pdf_chunks",
    client=client,
    embedding_function=_embedder,
)

# Shared owner for global (arXiv) docs
GLOBAL_OWNER = "GLOBAL"


def add_chunks_to_chroma(chunks, doc_id: str):

    if not settings.ENABLE_CHROMA or not chunks:
        return

    texts, metadatas, ids = [], [], []

    for i, c in enumerate(chunks):

        if isinstance(c, dict):
            content = c.get("page_content")
            metadata = c.get("metadata", {})
        else:
            content = getattr(c, "page_content", None)
            metadata = getattr(c, "metadata", {}) or {}

        if content is None:
            continue

        if not isinstance(content, str):
            content = str(content)

        cleaned = content.strip()

        if not cleaned:
            continue

        metadata_id = metadata.get("metadata_id")
        if not metadata_id:
            continue

        owner = metadata.get("user_id")
        owner = str(owner) if owner else GLOBAL_OWNER

        texts.append(cleaned)

        metadatas.append({
            "metadata_id": str(metadata_id),
            "user_id": owner,
            "section": metadata.get("section") or "body",
        })

        ids.append(f"{doc_id}_{i}")

    if texts:
        pdf_vector_store.add_texts(
            texts=texts,
            metadatas=metadatas,
            ids=ids,
        )


def semantic_search(
    query,
    n_results=5,
    metadata_id=None,
    user_id=None,
    section_priority=False,
):

    filters = []

    if metadata_id:
        filters.append({"metadata_id": str(metadata_id)})

    owner_filter = str(user_id) if user_id else GLOBAL_OWNER
    filters.append({"user_id": owner_filter})

    # --------------------------------------------------
    # Priority Search (abstract + introduction)
    # --------------------------------------------------

    if section_priority:
        priority_filters = filters + [
            {"section": {"$in": ["abstract", "introduction"]}}
        ]

        priority_filter = (
            priority_filters[0]
            if len(priority_filters) == 1
            else {"$and": priority_filters}
        )

        results = pdf_vector_store.similarity_search_with_score(
            query=str(query),
            k=n_results,
            filter=priority_filter,
        )

        if len(results) >= n_results:
            return [doc for doc, _ in results]

    # --------------------------------------------------
    # Fallback Search
    # --------------------------------------------------

    combined_filter = (
        filters[0]
        if len(filters) == 1
        else {"$and": filters}
    )

    results = pdf_vector_store.similarity_search_with_score(
        query=str(query),
        k=n_results,
        filter=combined_filter,
    )

    return [doc for doc, _ in results]