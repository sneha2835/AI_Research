from dotenv import load_dotenv
load_dotenv()

import os
import chromadb
from langchain_chroma import Chroma
from sentence_transformers import SentenceTransformer

# --------------------------------------------------
# Config
# --------------------------------------------------

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./vector_db")
EMBED_MODEL_NAME = os.getenv(
    "SENTENCE_EMBED_MODEL",
    "BAAI/bge-base-en-v1.5"
)

print(f"[Chroma] Persist directory: {PERSIST_DIR}")
print(f"[Chroma] Embedding model: {EMBED_MODEL_NAME}")

# --------------------------------------------------
# Embedding model (BGE – requires prefixes)
# --------------------------------------------------

embedding_model = SentenceTransformer(EMBED_MODEL_NAME)


class SentenceTransformerEmbedder:
    def __init__(self, model):
        self.model = model

    # NOTE: documents MUST be prefixed with "passage:"
    def embed_documents(self, texts):
        texts = [f"passage: {t}" for t in texts]
        return self.model.encode(
            texts,
            show_progress_bar=False,
            normalize_embeddings=True
        ).tolist()

    # NOTE: queries MUST be prefixed with "query:"
    def embed_query(self, text):
        text = f"query: {text}"
        return self.model.encode(
            [text],
            normalize_embeddings=True
        )[0].tolist()


embedder = SentenceTransformerEmbedder(embedding_model)

# --------------------------------------------------
# Chroma client (single persistent client)
# --------------------------------------------------

client = chromadb.Client(
    settings=chromadb.Settings(
        persist_directory=PERSIST_DIR,
        anonymized_telemetry=False,
    )
)

# --------------------------------------------------
# COLLECTION 1: PDF CHUNKS (user uploads)
# --------------------------------------------------

pdf_vector_store = Chroma(
    collection_name="pdf_chunks",
    client=client,
    embedding_function=embedder,
    persist_directory=PERSIST_DIR,
)


def add_chunks_to_chroma(
    text_chunks,
    doc_id: str,
    user_id: str | None = None,
):
    """
    Store PDF chunks in Chroma with scoped metadata.
    """

    texts = []
    metadatas = []
    ids = []

    for i, chunk in enumerate(text_chunks):
        texts.append(chunk.page_content)
        metadatas.append(
            {
                "metadata_id": doc_id,
                "user_id": user_id,
                "page_number": chunk.metadata.get("page", -1),
            }
        )
        ids.append(f"{doc_id}_{i}")

    if not texts:
        return

    pdf_vector_store.add_texts(
        texts=texts,
        metadatas=metadatas,
        ids=ids,
    )


def semantic_search(
    query: str,
    n_results: int = 5,
    metadata_id: str | None = None,
    user_id: str | None = None,
):
    """
    Scoped semantic search over PDF chunks.
    """

    where = None

    if metadata_id and user_id:
        where = {
            "$and": [
                {"metadata_id": metadata_id},
                {"user_id": user_id},
            ]
        }
    elif metadata_id:
        where = {"metadata_id": metadata_id}
    elif user_id:
        where = {"user_id": user_id}

    return pdf_vector_store.similarity_search(
        query,
        k=n_results,
        filter=where,
    )

# --------------------------------------------------
# COLLECTION 2: RESEARCH PAPERS (arXiv)
# --------------------------------------------------

research_vector_store = Chroma(
    collection_name="research_papers",
    client=client,
    embedding_function=embedder,
    persist_directory=PERSIST_DIR,
)

# ---- DEBUG: show count at startup ----
try:
    count = research_vector_store._collection.count()
    print(f"[Chroma] research_papers count: {count}")
except Exception as e:
    print("[Chroma] count check failed:", e)


def add_research_abstracts(
    abstracts: list[str],
    metadatas: list[dict],
    ids: list[str],
):
    """
    Store arXiv paper abstracts for GLOBAL semantic search.
    """

    if not abstracts:
        return

    research_vector_store.add_texts(
        texts=abstracts,
        metadatas=metadatas,
        ids=ids,
    )


def search_research_papers(query: str, n_results: int = 5):
    """
    Semantic search over arXiv research papers.
    """
    return research_vector_store.similarity_search(
        query,
        k=n_results
    )
