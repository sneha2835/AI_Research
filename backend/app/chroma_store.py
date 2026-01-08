# backend/app/chroma_store.py

from dotenv import load_dotenv
load_dotenv()

import chromadb
from sentence_transformers import SentenceTransformer
from langchain_chroma import Chroma
from backend.app.config import settings

# --------------------------------------------------
# Config
# --------------------------------------------------

PERSIST_DIR = settings.CHROMA_PERSIST_DIR
EMBED_MODEL_NAME = settings.SENTENCE_EMBED_MODEL

# --------------------------------------------------
# Embedding model
# --------------------------------------------------

_embedding_model = SentenceTransformer(EMBED_MODEL_NAME)

class SentenceTransformerEmbedder:
    def __init__(self, model):
        self.model = model

    def embed_documents(self, texts):
        texts = [f"passage: {t}" for t in texts]
        return self.model.encode(
            texts, normalize_embeddings=True
        ).tolist()

    def embed_query(self, text):
        text = f"query: {text}"
        return self.model.encode(
            [text], normalize_embeddings=True
        )[0].tolist()

_embedder = SentenceTransformerEmbedder(_embedding_model)

# --------------------------------------------------
# Chroma client
# --------------------------------------------------

_client = None

def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.Client(
            settings=chromadb.Settings(
                persist_directory=PERSIST_DIR,
                anonymized_telemetry=False,
            )
        )
    return _client

# --------------------------------------------------
# PDF CHUNKS COLLECTION
# --------------------------------------------------

pdf_vector_store = Chroma(
    collection_name="pdf_chunks",
    client=get_chroma_client(),
    embedding_function=_embedder,
    persist_directory=PERSIST_DIR,
)

def add_chunks_to_chroma(chunks, doc_id: str, user_id=None):
    if not settings.ENABLE_CHROMA or not chunks:
        return

    texts, metadatas, ids = [], [], []

    for i, c in enumerate(chunks):
        texts.append(c.page_content)
        metadatas.append({
            "metadata_id": doc_id,
            "user_id": str(user_id) if user_id else None,
            "page": c.metadata.get("page", -1),
        })
        ids.append(f"{doc_id}_{i}")

    pdf_vector_store.add_texts(
        texts=texts,
        metadatas=metadatas,
        ids=ids,
    )

def semantic_search(query, n_results=5, metadata_id=None, user_id=None):
    where = {}
    if metadata_id:
        where["metadata_id"] = metadata_id
    if user_id:
        where["user_id"] = str(user_id)

    return pdf_vector_store.similarity_search(
        query=query,
        k=n_results,
        where=where if where else None,
    )

# --------------------------------------------------
# RESEARCH PAPERS COLLECTION
# --------------------------------------------------

research_vector_store = Chroma(
    collection_name="research_papers",
    client=get_chroma_client(),
    embedding_function=_embedder,
    persist_directory=PERSIST_DIR,
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
    return research_vector_store.similarity_search(query, k=n_results)
