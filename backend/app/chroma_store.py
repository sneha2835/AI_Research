# backend/app/chroma_store.py

from dotenv import load_dotenv
load_dotenv()

import os
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_chroma import Chroma
from backend.app.config import settings

# --------------------------------------------------
# Persistent Chroma directory
# --------------------------------------------------

PERSIST_DIR = settings.CHROMA_PERSIST_DIR
os.makedirs(PERSIST_DIR, exist_ok=True)

print("🔥 Chroma persist directory:", PERSIST_DIR)

# --------------------------------------------------
# Embedding model
# --------------------------------------------------

_embedding_model = SentenceTransformer(settings.SENTENCE_EMBED_MODEL)


class SentenceTransformerEmbedder:
    """
    Wrapper to match LangChain embedding interface.
    """

    def __init__(self, model):
        self.model = model

    def embed_documents(self, texts):
        texts = [f"passage: {t}" for t in texts]
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

    def embed_query(self, text):
        text = f"query: {text}"
        return self.model.encode(
            [text],
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0].tolist()


_embedder = SentenceTransformerEmbedder(_embedding_model)

# --------------------------------------------------
# Persistent Chroma client (single instance)
# --------------------------------------------------

client = chromadb.PersistentClient(path=PERSIST_DIR)

# --------------------------------------------------
# 📚 Research papers (arXiv abstracts)
# --------------------------------------------------

research_vector_store = Chroma(
    collection_name="research_papers",
    client=client,
    embedding_function=_embedder,
)


def add_research_abstracts(abstracts, metadatas, ids):
    """
    Adds arXiv abstracts to vector store.
    Metadata must include:
      - paper_id
      - source = 'arxiv'
    """
    if not settings.ENABLE_CHROMA or not abstracts:
        return

    research_vector_store.add_texts(
        texts=abstracts,
        metadatas=metadatas,
        ids=ids,
    )


def search_research_papers(query, n_results=5):
    return research_vector_store.similarity_search(
        query=query,
        k=min(n_results, 15),
    )

# --------------------------------------------------
# 📄 PDF chunks (uploads + arXiv)
# --------------------------------------------------

pdf_vector_store = Chroma(
    collection_name="pdf_chunks",
    client=client,
    embedding_function=_embedder,
)


def add_chunks_to_chroma(chunks, doc_id: str, user_id=None):
    """
    Stores PDF chunks with STRICT metadata normalization.
    """

    if not settings.ENABLE_CHROMA or not chunks:
        return

    texts, metadatas, ids = [], [], []

    for i, c in enumerate(chunks):
        # Accept both dicts and LangChain Documents
        if isinstance(c, dict):
            content = c.get("page_content")
            metadata = c.get("metadata", {})
        else:
            content = getattr(c, "page_content", None)
            metadata = getattr(c, "metadata", {}) or {}

        # Skip empty or invalid content
        if not content or not str(content).strip():
            continue

        metadata_id = metadata.get("metadata_id")
        if not metadata_id:
            # Hard safety: never index without document linkage
            continue

        texts.append(content)

        metadatas.append({
            "metadata_id": str(metadata_id),
            "user_id": str(metadata.get("user_id")) if metadata.get("user_id") else None,
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
    """
    Unified semantic search with optional filters.
    """

    filters = []

    if metadata_id:
        filters.append({"metadata_id": str(metadata_id)})
    if user_id is not None:   # <-- IMPORTANT FIX
        filters.append({"user_id": str(user_id)})


    # --------------------------------------------------
    # Priority search: abstract + introduction
    # --------------------------------------------------
    if section_priority:
        priority_filters = filters + [
            {"section": {"$in": ["abstract", "introduction"]}}
        ]

        if priority_filters:
            priority_filter = (
                priority_filters[0]
                if len(priority_filters) == 1
                else {"$and": priority_filters}
            )

            results = pdf_vector_store.similarity_search_with_score(
                query=query,
                k=n_results,
                filter=priority_filter,
            )

            if len(results) >= n_results:
                return [doc for doc, _ in results]

    # --------------------------------------------------
    # Normal search fallback
    # --------------------------------------------------
    combined_filter = None
    if filters:
        combined_filter = filters[0] if len(filters) == 1 else {"$and": filters}

    results = pdf_vector_store.similarity_search_with_score(
        query=query,
        k=n_results,
        filter=combined_filter,
    )

    return [doc for doc, _ in results]
