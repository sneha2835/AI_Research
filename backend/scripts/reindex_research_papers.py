# backend/scripts/reindex_research_papers.py

import re
from pymongo import MongoClient

from backend.app.config import settings
from backend.app.chroma_store import (
    add_research_abstracts,
    research_vector_store,
)


def clean_abstract(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def main():
    print("🔁 Re-indexing research papers into Chroma...")

    mongo = MongoClient(settings.MONGO_URL)
    db = mongo[settings.DB_NAME]

    papers = list(db.research_papers.find({}, {"abstract": 1}))

    if not papers:
        print("❌ No papers found")
        return

    # ✅ CORRECT way to clear Chroma collection
    print("🧹 Clearing existing Chroma index...")
    research_vector_store._collection.delete(ids=None)

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
            "user_id": None,
        })
        ids.append(pid)

    print(f"📐 Indexing {len(abstracts)} abstracts...")
    add_research_abstracts(abstracts, metadatas, ids)

    print("✅ Re-indexing complete")


if __name__ == "__main__":
    main()
