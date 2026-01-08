# backend/app/chroma_store.py

from dotenv import load_dotenv
load_dotenv()

import os
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_chroma import Chroma
from backend.app.config import settings

# --------------------------------------------------
# Ensure directory exists (force-create)
# --------------------------------------------------

PERSIST_DIR = settings.CHROMA_PERSIST_DIR
os.makedirs(PERSIST_DIR, exist_ok=True)

print("🔥 Chroma persist directory:", PERSIST_DIR)

# --------------------------------------------------
# Embedding model
# --------------------------------------------------

_embedding_model = SentenceTransformer(settings.SENTENCE_EMBED_MODEL)

class SentenceTransformerEmbedder:
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
# 🔥 Persistent Chroma client (THIS IS THE FIX)
# --------------------------------------------------

client = chromadb.PersistentClient(
    path=PERSIST_DIR,
)

# --------------------------------------------------
# Research papers (arXiv)
# --------------------------------------------------

research_vector_store = Chroma(
    collection_name="research_papers",
    client=client,
    embedding_function=_embedder,
)

def add_research_abstracts(abstracts, metadatas, ids):
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
# PDF chunks
# --------------------------------------------------

pdf_vector_store = Chroma(
    collection_name="pdf_chunks",
    client=client,
    embedding_function=_embedder,
)

def add_chunks_to_chroma(chunks, doc_id: str, user_id=None):
    if not settings.ENABLE_CHROMA or not chunks:
        return

    texts, metadatas, ids = [], [], []

    for i, c in enumerate(chunks):
        if not c.page_content or not c.page_content.strip():
            continue

        texts.append(c.page_content)
        metadatas.append({
            "metadata_id": str(doc_id),
            "user_id": str(user_id) if user_id else None,
        })
        ids.append(f"{doc_id}_{i}")

    if texts:
        pdf_vector_store.add_texts(
            texts=texts,
            metadatas=metadatas,
            ids=ids,
        )

def semantic_search(query, n_results=5, metadata_id=None, user_id=None):
    filters = []

    if metadata_id:
        filters.append({"metadata_id": str(metadata_id)})

    if user_id:
        filters.append({"user_id": str(user_id)})

    chroma_filter = None

    if len(filters) == 1:
        chroma_filter = filters[0]
    elif len(filters) > 1:
        chroma_filter = {"$and": filters}

    results = pdf_vector_store.similarity_search_with_score(
        query=query,
        k=min(n_results, 20),
        filter=chroma_filter,
    )

    # similarity_search_with_score returns (Document, score)
    return [doc for doc, _score in results]
