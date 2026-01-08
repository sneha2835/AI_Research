# backend/routers/papers.py

import aiohttp
import os
import uuid
from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.db import db
from backend.app.auth import get_current_user
from backend.app.chroma_store import search_research_papers
from backend.routers.pdf_chunking import extract_pdf_chunks

UPLOAD_DIR = "backend/pdf_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

papers_router = APIRouter(prefix="/papers", tags=["Papers"])

@papers_router.get("/recent")
async def get_recent_papers(limit: int = Query(10, ge=5, le=20), current_user=Depends(get_current_user)):
    papers = await db.research_papers.find(
        {}, {"title": 1, "abstract": 1, "published": 1, "pdf_url": 1}
    ).sort("published", -1).limit(limit).to_list(limit)

    for p in papers:
        p["_id"] = str(p["_id"])
    return papers

@papers_router.get("/search")
async def search_papers(
    q: str = Query(..., min_length=2),
    limit: int = Query(5, ge=3, le=15),
    current_user=Depends(get_current_user),
):
    results = search_research_papers(q, limit)

    paper_ids = []
    for r in results:
        pid = (r.metadata or {}).get("paper_id")
        if ObjectId.is_valid(pid):
            paper_ids.append(ObjectId(pid))

    if not paper_ids:
        return []

    papers = await db.research_papers.find(
        {"_id": {"$in": paper_ids}},
        {"title": 1, "abstract": 1, "published": 1, "pdf_url": 1},
    ).to_list(limit)

    paper_map = {str(p["_id"]): p for p in papers}

    ordered = []
    for pid in paper_ids:
        p = paper_map.get(str(pid))
        if p:
            p["_id"] = str(p["_id"])
            ordered.append(p)

    return ordered

@papers_router.post("/analyze/{paper_id}")
async def analyze_paper(paper_id: str, current_user=Depends(get_current_user)):
    paper = await db.research_papers.find_one({"_id": ObjectId(paper_id)})
    if not paper:
        raise HTTPException(404, "Paper not found")

    existing = await db.pdf_files.find_one({
        "source": "arxiv",
        "paper_id": paper_id,
        "user_id": current_user["_id"],
    })
    if existing:
        return {"metadata_id": str(existing["_id"]), "cached": True}

    async with aiohttp.ClientSession() as session:
        async with session.get(paper["pdf_url"]) as resp:
            if resp.status != 200:
                raise HTTPException(500, "PDF download failed")
            data = await resp.read()

    filename = f"{uuid.uuid4().hex}.pdf"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(data)

    result = await db.pdf_files.insert_one({
        "user_id": current_user["_id"],
        "filename": paper["title"][:100],
        "path": path,
        "source": "arxiv",
        "paper_id": paper_id,
        "uploaded_at": datetime.utcnow(),
    })

    await extract_pdf_chunks(str(result.inserted_id), current_user)
    return {"metadata_id": str(result.inserted_id), "cached": False}
