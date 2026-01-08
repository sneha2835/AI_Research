# backend/routers/papers.py

from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId
from datetime import datetime

from backend.app.db import db
from backend.app.auth import get_current_user
from backend.app.chroma_store import search_research_papers

papers_router = APIRouter(prefix="/papers", tags=["Papers"])


# ---------------------------------------------------------
# 1️⃣ Get top 5–10 recently published papers
# ---------------------------------------------------------

@papers_router.get("/recent")
async def get_recent_papers(
    limit: int = Query(10, ge=5, le=20),
    current_user=Depends(get_current_user),
):
    papers = await db.research_papers.find(
        {},
        {
            "title": 1,
            "abstract": 1,
            "published": 1,
            "pdf_url": 1,
        },
    ).sort("published", -1).limit(limit).to_list(length=limit)

    for p in papers:
        p["_id"] = str(p["_id"])

    return papers


# ---------------------------------------------------------
# 2️⃣ Semantic search over research papers
# ---------------------------------------------------------

@papers_router.get("/search")
async def search_papers(
    q: str = Query(..., min_length=2),
    limit: int = Query(5, ge=3, le=15),
    current_user=Depends(get_current_user),
):
    results = search_research_papers(q, n_results=limit)

    paper_ids = []

    for r in results:
        metadata = r.metadata or {}
        pid = metadata.get("paper_id")

        if pid:
            try:
                paper_ids.append(ObjectId(pid))
            except Exception:
                continue


    if not paper_ids:
        return []

    cursor = db.research_papers.find(
        {"_id": {"$in": paper_ids}},
        {
            "title": 1,
            "abstract": 1,
            "published": 1,
            "pdf_url": 1,
        },
    )

    papers = await cursor.to_list(length=limit)

    # Preserve ranking order from Chroma
    paper_map = {str(p["_id"]): p for p in papers}
    ordered = []

    for pid in paper_ids:
        p = paper_map.get(str(pid))
        if p:
            p["_id"] = str(p["_id"])
            ordered.append(p)

    return ordered


# ---------------------------------------------------------
# 3️⃣ Track a paper view (called when user opens a paper)
# ---------------------------------------------------------

@papers_router.post("/view/{paper_id}")
async def track_paper_view(
    paper_id: str,
    current_user=Depends(get_current_user),
):
    if not ObjectId.is_valid(paper_id):
        raise HTTPException(status_code=400, detail="Invalid paper ID")

    await db.recent_views.update_one(
        {
            "user_id": ObjectId(current_user["_id"]),
            "paper_id": ObjectId(paper_id),
        },
        {
            "$set": {
                "viewed_at": datetime.utcnow(),
                "source": "arxiv",
            }
        },
        upsert=True,
    )

    return {"status": "view recorded"}


# ---------------------------------------------------------
# 4️⃣ Get recently viewed papers (per user)
# ---------------------------------------------------------

@papers_router.get("/recently-viewed")
async def get_recently_viewed(
    limit: int = Query(10, ge=5, le=20),
    current_user=Depends(get_current_user),
):
    views = await db.recent_views.find(
        {"user_id": ObjectId(current_user["_id"])}
    ).sort("viewed_at", -1).limit(limit).to_list(length=limit)

    paper_ids = [v["paper_id"] for v in views]

    if not paper_ids:
        return []

    papers = await db.research_papers.find(
        {"_id": {"$in": paper_ids}},
        {
            "title": 1,
            "abstract": 1,
            "published": 1,
            "pdf_url": 1,
        },
    ).to_list(length=limit)

    paper_map = {str(p["_id"]): p for p in papers}

    ordered = []
    for v in views:
        p = paper_map.get(str(v["paper_id"]))
        if p:
            p["_id"] = str(p["_id"])
            ordered.append(p)

    return ordered
