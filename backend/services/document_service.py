# backend/services/document_service.py

from datetime import datetime
from bson import ObjectId
from backend.app.db import db


# ==================================================
# 📄 arXiv document (global, shared)
# ==================================================

async def get_or_create_arxiv_document(paper: dict) -> dict:
    """
    Global (shared) arXiv document.

    - Created ONCE per arXiv paper
    - Reused by all users
    - Safe against duplicate creation
    """

    external_id = str(paper["_id"])

    # ----------------------------------------------
    # 1️⃣ Try fast path: fetch existing document
    # ----------------------------------------------
    existing = await db.documents.find_one({
        "source": "arxiv",
        "external_id": external_id,
    })

    if existing:
        return existing

    # ----------------------------------------------
    # 2️⃣ Create new document (idempotent intent)
    # ----------------------------------------------
    doc = {
        "type": "pdf",
        "source": "arxiv",
        "title": paper.get("title"),
        "external_id": external_id,
        "path": None,
        "owner": None,
        "indexed": False,
        "processing": False,      # NEW
        "ready_for_chat": False,  # NEW
        "created_at": datetime.utcnow(),
    }

    try:
        result = await db.documents.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    except Exception:
        # ------------------------------------------
        # 3️⃣ Race condition fallback
        # Another request created it first
        # ------------------------------------------
        existing = await db.documents.find_one({
            "source": "arxiv",
            "external_id": external_id,
        })

        if existing:
            return existing

        # If still missing → real failure
        raise


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
