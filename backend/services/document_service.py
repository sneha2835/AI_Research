from datetime import datetime
from bson import ObjectId
from app.db import db


# ==================================================
# 📄 arXiv document (global, shared)
# ==================================================

async def get_or_create_arxiv_document(paper: dict) -> dict:

    external_id = str(paper["_id"])

    existing = await db.documents.find_one({
        "source": "arxiv",
        "external_id": external_id,
    })

    if existing:
        return existing

    doc = {
        "type": "pdf",
        "source": "arxiv",
        "title": paper.get("title"),
        "external_id": external_id,
        "path": None,
        "owner": None,
        "indexed": False,
        "processing": False,
        "ready_for_chat": False,
        "created_at": datetime.utcnow(),
    }

    try:
        result = await db.documents.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    except Exception:
        existing = await db.documents.find_one({
            "source": "arxiv",
            "external_id": external_id,
        })

        if existing:
            return existing

        raise


# ==================================================
# 📤 Uploaded document
# ==================================================

async def create_uploaded_document(
    filename: str,
    user_id: ObjectId,
) -> dict:

    doc = {
        "type": "pdf",
        "source": "upload",
        "title": filename,
        "external_id": None,
        "path": None,
        "owner": user_id,
        "indexed": False,
        "processing": False,
        "ready_for_chat": False,
        "created_at": datetime.utcnow(),
    }

    result = await db.documents.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc