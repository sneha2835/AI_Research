# backend/scripts/reindex_research_papers.py

from pymongo import MongoClient
from backend.app.config import settings
from backend.app.chroma_store import add_research_abstracts


def main():
    print("🔁 Re-indexing research papers into Chroma...")

    mongo = MongoClient(settings.MONGO_URL)
    db = mongo[settings.DB_NAME]

    papers = list(db.research_papers.find({}, {"abstract": 1}))

    if not papers:
        print("❌ No papers found")
        return

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
