# backend/routers/papers.py

import aiohttp
import os
from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.db import db
from backend.app.auth import get_current_user
from backend.app.chroma_store import search_research_papers
from backend.services.document_service import get_or_create_arxiv_document
from backend.services.pdf_service import extract_and_index_pdf

UPLOAD_DIR = "backend/pdf_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

papers_router = APIRouter(prefix="/papers", tags=["Papers"])


@papers_router.get("/recent")
async def get_recent_papers(
    limit: int = Query(10, ge=5, le=20),
    current_user=Depends(get_current_user),
):
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

    paper_ids = [
        ObjectId(r.metadata["paper_id"])
        for r in results
        if r.metadata and ObjectId.is_valid(r.metadata.get("paper_id"))
    ]

    papers = await db.research_papers.find(
        {"_id": {"$in": paper_ids}}
    ).to_list(limit)

    for p in papers:
        p["_id"] = str(p["_id"])

    return papers


@papers_router.post("/analyze/{paper_id}")
async def analyze_arxiv_paper(
    paper_id: str,
    current_user=Depends(get_current_user),
):
    paper = await db.research_papers.find_one({"_id": ObjectId(paper_id)})
    if not paper:
        raise HTTPException(404, "Paper not found")

    document = await get_or_create_arxiv_document(paper)

    if not document.get("path"):
        async with aiohttp.ClientSession() as session:
            async with session.get(paper["pdf_url"]) as resp:
                if resp.status != 200:
                    raise HTTPException(500, "PDF download failed")
                data = await resp.read()

        path = os.path.join(UPLOAD_DIR, f"{document['_id']}.pdf")
        with open(path, "wb") as f:
            f.write(data)

        await db.documents.update_one(
            {"_id": document["_id"]},
            {"$set": {"path": path}},
        )
        document["path"] = path

        await extract_and_index_pdf(document)

    await db.recent_views.update_one(
        {
            "user_id": current_user["_id"],
            "document_id": str(document["_id"]),
        },
        {"$set": {"viewed_at": datetime.utcnow()}},
        upsert=True,
    )

    return {"document_id": str(document["_id"])}
