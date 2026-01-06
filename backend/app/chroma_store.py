from dotenv import load_dotenv
load_dotenv()

import chromadb
from langchain_chroma import Chroma

from sentence_transformers import SentenceTransformer
import os

embedding_model = SentenceTransformer(os.getenv("SENTENCE_EMBED_MODEL", "BAAI/bge-base-en-v1.5"))


class SentenceTransformerEmbedder:
    def __init__(self, model):
        self.model = model

    def embed_documents(self, texts):
        return self.model.encode(texts, show_progress_bar=False).tolist()

    def embed_query(self, text):
        return self.model.encode([text], show_progress_bar=False)[0].tolist()


embedder = SentenceTransformerEmbedder(embedding_model)

client = chromadb.Client()

vector_store = Chroma(
    collection_name="pdf_chunks",
    client=client,
    embedding_function=embedder,
    persist_directory=os.getenv("CHROMA_PERSIST_DIR", "./chroma_persist")
)


# backend/app/chroma_store.py

def add_chunks_to_chroma(
    text_chunks,
    doc_id: str,
    user_id: str | None = None
):
    """
    Store PDF chunks in Chroma with proper metadata for scoped retrieval.
    """

    texts = []
    metadatas = []
    ids = []

    for i, chunk in enumerate(text_chunks):
        texts.append(chunk.page_content)

        metadatas.append({
            "metadata_id": doc_id,                 # PDF-level isolation
            "user_id": user_id,                    # User-level isolation
            "page_number": chunk.metadata.get("page", -1)
        })

        ids.append(f"{doc_id}_{i}")

    if not texts:
        return

    vector_store.add_texts(
        texts=texts,
        metadatas=metadatas,
        ids=ids
    )

    try:
        vector_store.persist()
    except Exception:
        pass


def semantic_search(
    query: str,
    n_results: int = 5,
    metadata_id: str | None = None,
    user_id: str | None = None,
):
    """
    Perform scoped semantic search over Chroma.
    """

    filters = {}

    if metadata_id:
        filters["metadata_id"] = metadata_id

    if user_id:
        filters["user_id"] = user_id

    if filters:
        return vector_store.similarity_search(
            query,
            k=n_results,
            filter=filters
        )

    return vector_store.similarity_search(query, k=n_results)
