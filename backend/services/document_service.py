# backend/services/document_service.py

from datetime import datetime
from bson import ObjectId
from backend.app.db import db


async def get_or_create_arxiv_document(paper: dict) -> dict:
    """
    Global (shared) arXiv document.
    Created once, reused by all users.
    """

    existing = await db.documents.find_one({
        "source": "arxiv",
        "external_id": str(paper["_id"]),
    })

    if existing:
        return existing

    doc = {
    "type": "pdf",
    "source": "arxiv",
    "title": paper["title"],
    "external_id": str(paper["_id"]),
    "path": None,
    "owner": None,
    "indexed": False,   # ✅ ADD THIS
    "created_at": datetime.utcnow(),
}


    result = await db.documents.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


