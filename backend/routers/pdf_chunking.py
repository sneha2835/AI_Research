from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from backend.app.db import db
from backend.app.auth import get_current_user
from backend.app.chroma_store import semantic_search
from backend.app.llm_inference import answer_from_context, summarize_text
from backend.services.document_service import create_uploaded_document
from backend.services.pdf_service import extract_and_index_pdf
from backend.schemas.pdf import AskPdfRequest, SummarizePdfRequest

import os
import re

pdf_router = APIRouter(prefix="/pdf", tags=["PDF"])

UPLOAD_DIR = "backend/pdf_uploads"
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

    document = await create_uploaded_document(
        filename=file.filename,
        user_id=current_user["_id"],
    )

    path = os.path.join(UPLOAD_DIR, f"{document['_id']}.pdf")
    file_bytes = await file.read()

    with open(path, "wb") as f:
        f.write(file_bytes)

    await db.documents.update_one(
        {"_id": document["_id"]},
        {"$set": {"path": path, "size_bytes": len(file_bytes)}},
    )

    if not document.get("indexed"):
        await extract_and_index_pdf({
            "_id": document["_id"],
            "path": path,
            "owner": current_user["_id"],
        })

    # 🕘 Log recent view (upload)
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
# 📂 List user uploads
# ==================================================

@pdf_router.get("/my_uploads")
async def get_my_uploads(current_user=Depends(get_current_user)):
    docs = await db.documents.find(
        {
            "owner": current_user["_id"],
            "source": "upload",
        }
    ).sort("created_at", -1).to_list(100)

    for d in docs:
        d["_id"] = str(d["_id"])

    return docs

# ==================================================
# 🗑️ Delete uploaded PDF
# ==================================================

@pdf_router.delete("/delete/{document_id}")
async def delete_pdf(
    document_id: str,
    current_user=Depends(get_current_user),
):
    if not ObjectId.is_valid(document_id):
        raise HTTPException(400, "Invalid document id")

    await db.documents.delete_one(
        {
            "_id": ObjectId(document_id),
            "owner": current_user["_id"],
        }
    )

    await db.chat_history.delete_many(
        {
            "document_id": ObjectId(document_id),
            "user_id": current_user["_id"],
        }
    )

    await db.recent_views.delete_many(
        {
            "document_id": ObjectId(document_id),
            "user_id": current_user["_id"],
        }
    )

    return {"status": "deleted"}

# ==================================================
# ❓ Ask PDF (Q&A)
# ==================================================

@pdf_router.post("/ask")
async def ask_pdf(
    payload: AskPdfRequest,
    current_user=Depends(get_current_user),
):
    if not ObjectId.is_valid(payload.document_id):
        raise HTTPException(400, "Invalid document id")

    document = await db.documents.find_one({
        "_id": ObjectId(payload.document_id),
        "$or": [
            {"owner": current_user["_id"]},
            {"owner": None},
        ],
    })

    if not document:
        raise HTTPException(404, "Document not found")

    source = "arxiv" if document.get("source") == "arxiv" else "upload"

    chunks = semantic_search(
        query=payload.query,
        metadata_id=payload.document_id,
        n_results=payload.n_results,
        user_id=document.get("owner"),
        section_priority=True,
    )

    valid_chunks = [
        c for c in chunks
        if c.page_content and not is_junk_chunk(c.page_content)
    ]

    valid_chunks = deduplicate_chunks(valid_chunks, payload.n_results)

    if not valid_chunks:
        answer = "No relevant content found in this document."
    else:
        context = "\n\n".join(c.page_content for c in valid_chunks)[:3500]

        prompt = f"""
Based on the context below, answer the question clearly and concisely.

Context:
{context}

Question:
{payload.query}

Answer:
""".strip()

        answer = answer_from_context(prompt) or "I couldn't generate an answer."

    timestamp = datetime.utcnow()

    # ✅ SINGLE, AUTHORITATIVE CHAT SAVE
    await db.chat_history.insert_many([
        {
            "document_id": ObjectId(payload.document_id),
            "user_id": current_user["_id"],
            "role": "user",
            "type": "qa",
            "content": payload.query,
            "source": source,
            "timestamp": timestamp,
        },
        {
            "document_id": ObjectId(payload.document_id),
            "user_id": current_user["_id"],
            "role": "assistant",
            "type": "qa",
            "content": answer,
            "source": source,
            "timestamp": timestamp,
        },
    ])

    return {"answer": answer}

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

    document = await db.documents.find_one({
        "_id": ObjectId(payload.document_id),
        "$or": [
            {"owner": current_user["_id"]},
            {"owner": None},
        ],
    })

    if not document:
        raise HTTPException(404, "Document not found")

    chunks = semantic_search(
        query="Summarize the main contributions of this paper",
        metadata_id=payload.document_id,
        n_results=12,
        user_id=document.get("owner"),
        section_priority=True,
    )

    valid_chunks = [
        c for c in chunks
        if c.page_content and not is_junk_chunk(c.page_content)
    ]

    valid_chunks = deduplicate_chunks(valid_chunks, 10)

    if not valid_chunks:
        summary = "No readable content found."
    else:
        context = "\n\n".join(c.page_content for c in valid_chunks)[:4000]

        prompt = f"""
Summarize the following academic paper using this structure:

Objective:
Problem Statement:
Methodology:
Key Findings:
Conclusion:

Text:
{context}
""".strip()

        summary = summarize_text(prompt) or "Summary generation failed."

    # ✅ SINGLE SAVE (summary only)
    await db.chat_history.insert_one({
        "document_id": ObjectId(payload.document_id),
        "user_id": current_user["_id"],
        "role": "assistant",
        "type": "summary",
        "content": summary,
        "source": document.get("source"),
        "timestamp": datetime.utcnow(),
    })

    return {"summary": summary}
