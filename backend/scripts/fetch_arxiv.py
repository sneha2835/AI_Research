import arxiv
from datetime import datetime
from pymongo import MongoClient

from backend.app.config import settings
from backend.app.chroma_store import add_research_abstracts

MAX_PAPERS = 150

CATEGORIES = [
    "cs.AI",
    "cs.CL",
    "cs.LG",
    "stat.ML",
    "cs.CV",
    "cs.IR",
]

mongo = MongoClient(settings.MONGO_URL)
db = mongo[settings.DB_NAME]


def fetch_arxiv_papers():
    query = " OR ".join(f"cat:{c}" for c in CATEGORIES)
    search = arxiv.Search(
        query=query,
        max_results=MAX_PAPERS,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    return list(search.results())


def main():
    print("🔍 Fetching arXiv papers...")
    results = fetch_arxiv_papers()

    abstracts, metadatas, ids = [], [], []
    inserted, skipped = 0, 0

    for paper in results:
        if db.research_papers.find_one({"pdf_url": paper.pdf_url}):
            skipped += 1
            continue

        doc = {
            "title": paper.title.strip(),
            "abstract": paper.summary.replace("\n", " ").strip(),
            "categories": paper.categories,
            "published": paper.published,
            "pdf_url": paper.pdf_url,
            "source": "arxiv",
            "created_at": datetime.utcnow(),
        }

        result = db.research_papers.insert_one(doc)
        pid = str(result.inserted_id)

        abstracts.append(doc["abstract"])
        metadatas.append({
            "paper_id": pid,
            "source": "arxiv",
            "user_id": None,
        })
        ids.append(pid)
        inserted += 1

    add_research_abstracts(abstracts, metadatas, ids)

    print("\n✅ Ingestion complete")
    print(f"Inserted: {inserted}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()
