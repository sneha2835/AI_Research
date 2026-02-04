import os
from dotenv import load_dotenv
load_dotenv()

import chromadb
from sentence_transformers import SentenceTransformer
from langchain_chroma import Chroma

from backend.app.config import settings

# ==================================================
# 📁 Persistent directory
# ==================================================

PERSIST_DIR = settings.CHROMA_PERSIST_DIR
os.makedirs(PERSIST_DIR, exist_ok=True)

print("🔥 Chroma persist directory:", os.path.abspath(PERSIST_DIR))

# ==================================================
# 🔤 Embedding model
# ==================================================

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

# ==================================================
# 🧠 Persistent Chroma client
# ==================================================

client = chromadb.PersistentClient(path=PERSIST_DIR)

# ==================================================
# 📚 arXiv abstracts (global search)
# ==================================================

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

def search_research_papers(query: str, n_results: int = 5):
    return research_vector_store.similarity_search(
        query=query,
        k=min(n_results, 15),
    )

# ==================================================
# 📄 PDF chunks (arXiv + uploads)
# ==================================================

pdf_vector_store = Chroma(
    collection_name="pdf_chunks",
    client=client,
    embedding_function=_embedder,
)

def add_chunks_to_chroma(chunks, doc_id: str):
    if not settings.ENABLE_CHROMA or not chunks:
        return

    texts, metadatas, ids = [], [], []

    for i, c in enumerate(chunks):
        content = getattr(c, "page_content", None)
        metadata = getattr(c, "metadata", {})

        if not content or not str(content).strip():
            continue

        texts.append(content)
        metadatas.append({
            "metadata_id": str(metadata.get("metadata_id")),
            "user_id": metadata.get("user_id"),
            "section": metadata.get("section", "body"),
        })
        ids.append(f"{doc_id}_{i}")

    if texts:
        pdf_vector_store.add_texts(
            texts=texts,
            metadatas=metadatas,
            ids=ids,
        )

# ==================================================
# 🔍 Document-scoped semantic search
# ==================================================

def semantic_search(
    query,
    n_results=5,
    metadata_id=None,
    user_id=None,
    section_priority=False,
):
    """
    Document-scoped semantic search.
    """

    # 🚫 Guard against empty query
    if not query.strip():
        return []

    filters = {}

    if metadata_id:
        filters["metadata_id"] = str(metadata_id)

    if user_id:
        filters["user_id"] = str(user_id)

    # ==================================================
    # 🔥 Priority search (abstract / intro)
    # ==================================================
    if section_priority:
        priority_filters = filters.copy()
        priority_filters["section"] = {"$in": ["abstract", "introduction"]}

        prioritized = pdf_vector_store.similarity_search_with_score(
            query=query,
            k=n_results,
            filter=priority_filters if priority_filters else None,
        )

        if len(prioritized) >= n_results:
            return [doc for doc, _ in prioritized]

    # ==================================================
    # 🔁 Fallback search
    # ==================================================
    results = pdf_vector_store.similarity_search_with_score(
        query=query,
        k=n_results,
        filter=filters if filters else None,
    )

    return [doc for doc, _ in results]

