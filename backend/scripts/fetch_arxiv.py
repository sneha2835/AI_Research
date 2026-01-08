# backend/scripts/reindex_research_papers.py

import re
from pymongo import MongoClient

from backend.app.config import settings
from backend.app.chroma_store import (
    add_research_abstracts,
    research_vector_store,
)


def clean_abstract(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clear_chroma_collection():
    """
    Safely delete ALL embeddings from the Chroma collection.
    """
    collection = research_vector_store._collection

    result = collection.get(include=[])
    ids = result.get("ids", [])

    if not ids:
        print("ℹ️ Chroma collection already empty")
        return

    collection.delete(ids=ids)
    print(f"🧹 Deleted {len(ids)} embeddings from Chroma")


def main():
    print("🔁 Re-indexing research papers into Chroma...")

    mongo = MongoClient(settings.MONGO_URL)
    db = mongo[settings.DB_NAME]

    papers = list(db.research_papers.find({}, {"abstract": 1}))

    if not papers:
        print("❌ No papers found")
        return

    print("🧹 Clearing existing Chroma index...")
    clear_chroma_collection()

    abstracts, metadatas, ids = [], [], []

    for p in papers:
        if not p.get("abstract"):
            continue

        abstract = clean_abstract(p["abstract"])
        pid = str(p["_id"])

        abstracts.append(abstract)
        metadatas.append({
            "paper_id": pid,
            "source": "arxiv",
        })
        ids.append(pid)

    print(f"📐 Indexing {len(abstracts)} abstracts...")
    add_research_abstracts(abstracts, metadatas, ids)

    print("✅ Re-indexing complete")


if __name__ == "__main__":
    main()
