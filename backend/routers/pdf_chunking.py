from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.db import db
from app.auth import get_current_user
from app.chroma_store import semantic_search
from app.llm_inference import generate_text, generate_followups
from services.document_service import create_uploaded_document
from services.pdf_service import extract_and_index_pdf
from services.reranker import rerank
from schemas.pdf import AskPdfRequest, SummarizePdfRequest

import os
import re

pdf_router = APIRouter(prefix="/pdf", tags=["PDF"])

UPLOAD_DIR = "pdf_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ==================================================
# 🔧 Helpers
# ==================================================

def is_junk_chunk(text: str) -> bool:
    text = text.strip()
    if len(text) < 30:
        return True
    if re.fullmatch(r"\[\d+\]", text):
        return True
    return False


def deduplicate_chunks(chunks, max_chunks):
    seen = set()
    unique = []

    for c in chunks:
        key = c.page_content.strip()[:200]
        if key not in seen:
            seen.add(key)
            unique.append(c)
        if len(unique) >= max_chunks:
            break

    return unique


# ==================================================
# 📤 Upload PDF
# ==================================================

@pdf_router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are allowed")

    user_id = current_user["_id"]

    existing = await db.documents.find_one({
        "owner": user_id,
        "title": file.filename,
        "source": "upload"
    })

    if existing:
        return {
            "document_id": str(existing["_id"]),
            "status": "already_exists",
        }

    document = await create_uploaded_document(
        filename=file.filename,
        user_id=user_id,
    )

    path = os.path.join(UPLOAD_DIR, f"{document['_id']}.pdf")
    file_bytes = await file.read()

    with open(path, "wb") as f:
        f.write(file_bytes)

    await db.documents.update_one(
        {"_id": document["_id"]},
        {
            "$set": {
                "path": path,
                "size_bytes": len(file_bytes),
                "processing": True
            }
        },
    )

    await extract_and_index_pdf({
        "_id": document["_id"],
        "path": path,
        "owner": user_id,
    })

    await db.documents.update_one(
        {"_id": document["_id"]},
        {
            "$set": {
                "ready_for_chat": True,
                "indexed": True,
                "processing": False
            }
        }
    )
    # Add to recent views
    await db.recent_views.update_one(
        {
            "user_id": current_user["_id"],
            "type": "upload",
            "document_id": document["_id"],
        },
        {
            "$set": {
                "title": document["title"],
                "viewed_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )

    return {
        "document_id": str(document["_id"]),
        "status": "uploaded",
    }

# ==================================================
# 📂 Get My Uploaded PDFs
# ==================================================

@pdf_router.get("/my_uploads")
async def get_my_uploads(current_user=Depends(get_current_user)):

    uploads = await db.documents.find(
        {
            "owner": current_user["_id"],
            "source": "upload"
        }
    ).sort("created_at", -1).to_list(100)

    for u in uploads:
        u["_id"] = str(u["_id"])

    return uploads


# ==================================================
# ❓ Ask PDF
# ==================================================

@pdf_router.post("/ask")
async def ask_pdf(
    payload: AskPdfRequest,
    current_user=Depends(get_current_user),
):

    if not ObjectId.is_valid(payload.document_id):
        raise HTTPException(400, "Invalid document id")

    doc_id = ObjectId(payload.document_id)

    document = await db.documents.find_one({
        "_id": doc_id,
        "$or": [
            {"owner": current_user["_id"]},
            {"owner": None},
        ],
    })

    if not document:
        raise HTTPException(404, "Document not found")

    if document.get("processing") or not document.get("ready_for_chat"):
        raise HTTPException(409, "Document still processing")

    owner = document.get("owner")

    chunks = semantic_search(
        query=payload.query,
        metadata_id=payload.document_id,
        n_results=20,
        user_id=str(owner) if owner else None,
        section_priority=True,
    )

    valid_chunks = [
        c for c in chunks
        if c.page_content
        and not is_junk_chunk(c.page_content)
    ]

    valid_chunks = deduplicate_chunks(valid_chunks, 20)
    valid_chunks = rerank(payload.query, valid_chunks, top_k=8)

    fallback_text = "This paper does not contain that information. Would you like me to search the web?"

    if not valid_chunks:
        answer = fallback_text
        followups = []
        needs_web_search = True
    else:
        context = "\n\n".join(c.page_content[:600] for c in valid_chunks[:3])

        prompt = f"""
Answer the research question using ONLY the context below.

If answer not present, reply exactly:
{fallback_text}

Context:
{context}

Question:
{payload.query}

Answer:
""".strip()

        answer = (generate_text(prompt) or "").strip()

        needs_web_search = answer.startswith("This paper does not contain")

        if needs_web_search:
            answer = fallback_text
            followups = []
        else:
            followups = generate_followups(payload.query, answer)

    timestamp = datetime.utcnow()

    await db.chat_history.insert_many([
        {
            "document_id": doc_id,
            "user_id": current_user["_id"],
            "role": "user",
            "type": "qa",
            "content": payload.query,
            "timestamp": timestamp,
        },
        {
            "document_id": doc_id,
            "user_id": current_user["_id"],
            "role": "assistant",
            "type": "qa",
            "content": answer,
            "timestamp": timestamp,
        },
    ])

    view_type = "upload" if document.get("owner") else "arxiv"
    await db.recent_views.update_one(
    {
        "user_id": current_user["_id"],
        "type": "view_type",
        "document_id": ObjectId(payload.document_id),
    },
    {
        "$set": {
            "title": document["title"],
            "viewed_at": datetime.utcnow(),
        }
    },
    upsert=True,
    )

    return {
        "answer": answer,
        "followups": followups,
        "needs_web_search": needs_web_search
    }


# ==================================================
# 📝 Summarize PDF
# ==================================================

@pdf_router.post("/summarize")
async def summarize_pdf(
    payload: SummarizePdfRequest,
    current_user=Depends(get_current_user),
):

    if not ObjectId.is_valid(payload.document_id):
        raise HTTPException(400, "Invalid document id")

    doc_id = ObjectId(payload.document_id)

    document = await db.documents.find_one({
        "_id": doc_id,
        "$or": [
            {"owner": current_user["_id"]},
            {"owner": None},
        ],
    })

    if not document:
        raise HTTPException(404, "Document not found")

    owner = document.get("owner")

    chunks = semantic_search(
        query="Summarize the main contributions of this paper",
        metadata_id=payload.document_id,
        n_results=15,
        user_id=str(owner) if owner else None,
        section_priority=True,
    )

    valid_chunks = [
        c for c in chunks
        if c.page_content and not is_junk_chunk(c.page_content)
    ]

    valid_chunks = deduplicate_chunks(valid_chunks, 12)

    if not valid_chunks:
        summary = "No readable content found."
    else:
        context = "\n\n".join(c.page_content[:800] for c in valid_chunks[:4])

        prompt = f"""
Summarize the research paper using this format:

Objective:
Problem Being Addressed:
Methodology:
Key Findings:
Conclusion:
Limitations:

Text:
{context}
""".strip()

        summary = generate_text(prompt) or "Summary generation failed."

    await db.chat_history.insert_one({
        "document_id": doc_id,
        "user_id": current_user["_id"],
        "role": "assistant",
        "type": "summary",
        "content": summary,
        "timestamp": datetime.utcnow(),
    })

    view_type = "upload" if document.get("owner") else "arxiv"
    await db.recent_views.update_one(
    {
        "user_id": current_user["_id"],
        "type": "view_type",
        "document_id": ObjectId(payload.document_id),
    },
    {
        "$set": {
            "title": document["title"],
            "viewed_at": datetime.utcnow(),
        }
    },
    upsert=True,
    )
    return {"summary": summary}