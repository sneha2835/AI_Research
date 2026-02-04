from datetime import datetime
from bson import ObjectId
from backend.app.db import db


# ==================================================
# 📄 arXiv document (global, shared)
# ==================================================

async def get_or_create_arxiv_document(paper: dict) -> dict:
    """
    Global (shared) arXiv document.
    Created once and reused by all users.
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
        "indexed": False,
        "created_at": datetime.utcnow(),
    }

    result = await db.documents.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


# ==================================================
# 📤 Uploaded document (user-owned)
# ==================================================

async def create_uploaded_document(
    filename: str,
    user_id: ObjectId,
) -> dict:
    """
    Creates a document entry for a user-uploaded PDF.
    """

    doc = {
        "type": "pdf",
        "source": "upload",
        "title": filename,
        "external_id": None,
        "path": None,
        "owner": user_id,
        "indexed": False,
        "created_at": datetime.utcnow(),
    }

    result = await db.documents.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc
