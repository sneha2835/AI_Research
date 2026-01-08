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
        "path": None,              # filled after PDF download
        "owner": None,             # GLOBAL
        "created_at": datetime.utcnow(),
    }

    result = await db.documents.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


async def create_uploaded_document(
    filename: str,
    path: str,
    user_id: str,
) -> dict:
    doc = {
        "type": "pdf",
        "source": "upload",
        "title": filename,
        "external_id": None,
        "path": path,
        "owner": user_id,
        "created_at": datetime.utcnow(),
    }

    result = await db.documents.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc
