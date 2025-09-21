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


def add_chunks_to_chroma(text_chunks, doc_id: str):
    texts = [chunk.page_content for chunk in text_chunks]
    metadatas = [{"page_number": chunk.metadata.get("page", -1)} for chunk in text_chunks]
    ids = [f"{doc_id}_{i}" for i in range(len(text_chunks))]

    vector_store.add_texts(texts=texts, metadatas=metadatas, ids=ids)

    try:
        vector_store.persist()
    except Exception:
        pass


def semantic_search(query: str, n_results=5):
    return vector_store.similarity_search(query, k=n_results)
