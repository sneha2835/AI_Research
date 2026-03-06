# backend/scripts/reindex_research_papers.py

from pymongo import MongoClient
from app.config import settings
from app.chroma_store import add_research_abstracts
from app.chroma_store import research_vector_store

def main():
    print("🔁 Re-indexing research papers into Chroma...")

    mongo = MongoClient(settings.MONGO_URL)
    db = mongo[settings.DB_NAME]

    papers = list(db.research_papers.find({}, {"abstract": 1}))

    if not papers:
        print("❌ No papers found")
        return

    print("🧹 Clearing existing research_papers collection...")
    research_vector_store.delete(where={})

    abstracts, metadatas, ids = [], [], []

    for p in papers:
        if not p.get("abstract"):
            continue

        pid = str(p["_id"])

        abstracts.append(p["abstract"])
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
