# backend/routers/pdf_chunking.py

from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from backend.app.db import db
from backend.app.auth import get_current_user
from backend.app.chroma_store import semantic_search
from backend.services.pdf_service import extract_and_index_pdf
from backend.services.llm_service import answer_from_context
import os
from typing import List
from fastapi import UploadFile, File

pdf_router = APIRouter(prefix="/pdf", tags=["PDF"])

UPLOAD_DIR = "backend/pdf_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --------------------------------------------------
# Upload PDF
# --------------------------------------------------

@pdf_router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are allowed")

    document = {
        "owner": current_user["_id"],
        "title": file.filename,
        "created_at": datetime.utcnow(),
        "path": None,
    }

    result = await db.documents.insert_one(document)
    document["_id"] = result.inserted_id

    path = os.path.join(UPLOAD_DIR, f"{document['_id']}.pdf")

    with open(path, "wb") as f:
        f.write(await file.read())

    await db.documents.update_one(
        {"_id": document["_id"]},
        {"$set": {"path": path}},
    )

    await extract_and_index_pdf({
        "_id": document["_id"],
        "path": path,
        "owner": current_user["_id"],
    })

    return {
        "document_id": str(document["_id"]),
        "status": "uploaded",
    }

# --------------------------------------------------
# Ask PDF
# --------------------------------------------------

@pdf_router.post("/ask")
async def ask_pdf(payload: dict, current_user=Depends(get_current_user)):
    document_id = payload.get("document_id")
    query = payload.get("query")
    n_results = payload.get("n_results", 5)

    if not document_id or not query:
        raise HTTPException(400, "document_id and query are required")

    document = await db.documents.find_one({"_id": ObjectId(document_id)})
    if not document:
        raise HTTPException(404, "Document not found")

    chunks = semantic_search(
        query=query,
        n_results=max(n_results, 8),
        metadata_id=document_id,
        user_id=document.get("owner"),
    )

    valid_chunks = [
        c for c in chunks if getattr(c, "page_content", "").strip()
    ]

    if not valid_chunks:
        return {"answer": "No readable content found in this PDF."}

    context = "\n\n".join(
        c.page_content[:500] for c in valid_chunks
    )[:3000]

    prompt = f"""
Answer ONLY using the context below.

Context:
{context}

Question:
{query}

Answer:
""".strip()

    answer = answer_from_context(prompt)

    return {"answer": answer}

# --------------------------------------------------
# Summarize PDF
# --------------------------------------------------

@pdf_router.post("/summarize")
async def summarize_pdf(payload: dict, current_user=Depends(get_current_user)):
    document_id = payload.get("document_id")

    if not document_id:
        raise HTTPException(400, "document_id is required")

    document = await db.documents.find_one({"_id": ObjectId(document_id)})
    if not document:
        raise HTTPException(404, "Document not found")

    chunks = semantic_search(
        query="Summarize this document",
        n_results=12,
        metadata_id=document_id,
        user_id=document.get("owner"),
    )

    valid_chunks = [
        c for c in chunks if getattr(c, "page_content", "").strip()
    ]

    if not valid_chunks:
        return {"summary": "No readable content found in this PDF."}

    context = "\n\n".join(
        c.page_content[:500] for c in valid_chunks
    )[:3000]

    prompt = f"""
Summarize the following document clearly and concisely.

Content:
{context}

Summary:
""".strip()

    summary = answer_from_context(prompt)

    return {"summary": summary}
