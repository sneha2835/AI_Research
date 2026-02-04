from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.db import db
from backend.app.auth import get_current_user
from backend.app.chroma_store import search_research_papers
from backend.services.document_service import get_or_create_arxiv_document
from backend.services.pdf_service import extract_and_index_pdf

import aiohttp
import os

papers_router = APIRouter(prefix="/papers", tags=["Papers"])

UPLOAD_DIR = "backend/pdf_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==================================================
# 🔥 Recent arXiv papers (Dashboard)
# ==================================================

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
    ).sort("published", -1).limit(limit).to_list(limit)

    for p in papers:
        p["_id"] = str(p["_id"])

    return papers

# ==================================================
# 🔍 Semantic search over arXiv abstracts
# ==================================================

@papers_router.get("/search")
async def search_papers(
    q: str = Query(..., min_length=2),
    limit: int = Query(5, ge=3, le=15),
    current_user=Depends(get_current_user),
):
    """
    Semantic search ONLY over arXiv abstracts.
    Does NOT touch full PDFs.
    """

    try:
        results = search_research_papers(q, limit)
    except Exception:
        return []

    paper_ids = []

    for r in results:
        meta = r.metadata or {}
        pid = meta.get("paper_id")
        if pid and ObjectId.is_valid(pid):
            paper_ids.append(ObjectId(pid))

    if not paper_ids:
        return []

    papers = await db.research_papers.find(
        {"_id": {"$in": paper_ids}}
    ).to_list(limit)

    for p in papers:
        p["_id"] = str(p["_id"])

    return papers

# ==================================================
# 📄 Paper details (CLICK → VIEW ABSTRACT)
# ==================================================

@papers_router.get("/{paper_id}")
async def get_paper_details(
    paper_id: str,
    current_user=Depends(get_current_user),
):
    if not ObjectId.is_valid(paper_id):
        raise HTTPException(400, "Invalid paper id")

    paper = await db.research_papers.find_one({"_id": ObjectId(paper_id)})
    if not paper:
        raise HTTPException(404, "Paper not found")

    paper["_id"] = str(paper["_id"])
    return paper

# ==================================================
# 🧠 Analyze / process arXiv paper
# ==================================================

@papers_router.post("/analyze/{paper_id}")
async def analyze_arxiv_paper(
    paper_id: str,
    current_user=Depends(get_current_user),
):
    """
    Converts an arXiv paper into a document.
    After this step, arXiv == uploaded PDF.
    """

    if not ObjectId.is_valid(paper_id):
        raise HTTPException(400, "Invalid paper id")

    paper = await db.research_papers.find_one({"_id": ObjectId(paper_id)})
    if not paper:
        raise HTTPException(404, "Paper not found")

    # 🔑 Get or create unified document
    document = await get_or_create_arxiv_document(paper)

    # ==================================================
    # 📥 Download + index PDF (only once)
    # ==================================================

    if not document.get("indexed"):
        async with aiohttp.ClientSession() as session:
            async with session.get(paper["pdf_url"]) as resp:
                if resp.status != 200:
                    raise HTTPException(500, "Failed to download PDF")
                pdf_bytes = await resp.read()

        pdf_path = os.path.join(UPLOAD_DIR, f"{document['_id']}.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_bytes)

        await db.documents.update_one(
            {"_id": document["_id"]},
            {"$set": {"path": pdf_path}},
        )

        document["path"] = pdf_path
        await extract_and_index_pdf(document)

    # ==================================================
    # 🕘 Log recent view (arXiv)
    # ==================================================

    await db.recent_views.update_one(
        {
            "user_id": current_user["_id"],
            "type": "arxiv",
            "paper_id": paper_id,
        },
        {
            "$set": {
                "title": paper["title"],
                "abstract": paper.get("abstract"),
                "published": paper.get("published"),
                "document_id": document["_id"],
                "viewed_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )

    return {
        "document_id": str(document["_id"]),
    }

# ==================================================
# 🔁 Alias (frontend compatibility)
# ==================================================

@papers_router.post("/process/{paper_id}")
async def process_arxiv_paper(
    paper_id: str,
    current_user=Depends(get_current_user),
):
    return await analyze_arxiv_paper(paper_id, current_user)

# ==================================================
# 🕘 Recently viewed (mixed list)
# ==================================================

@papers_router.get("/recently-viewed")
async def get_recently_viewed(
    limit: int = Query(10, ge=1, le=20),
    current_user=Depends(get_current_user),
):
    views = await db.recent_views.find(
        {"user_id": current_user["_id"]}
    ).sort("viewed_at", -1).limit(limit).to_list(limit)

    results = []

    for v in views:
        item = {
            "type": v.get("type"),
            "title": v.get("title"),
            "viewed_at": v.get("viewed_at"),
        }

        if v.get("type") == "arxiv":
            item.update({
                "_id": v.get("paper_id"),
                "abstract": v.get("abstract"),
                "published": v.get("published"),
                "document_id": str(v.get("document_id")),
            })
        else:
            item.update({
                "_id": str(v.get("document_id")),
            })

        results.append(item)

    return results
