# backend/routers/pdf_chunking.py

import os
import uuid
import aiofiles
from bson import ObjectId
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel

from backend.app.auth import get_current_user
from backend.app.db import db
from backend.app.chroma_store import semantic_search
from backend.app.llm_inference import answer_from_context, summarize_text
from backend.services.document_service import create_uploaded_document
from backend.services.pdf_service import extract_and_index_pdf

pdf_router = APIRouter(prefix="/pdf", tags=["PDF"])

UPLOAD_DIR = "backend/pdf_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -------------------------
# Models
# -------------------------

class AskRequest(BaseModel):
    document_id: str
    query: str
    n_results: int = 5

class SummarizeRequest(BaseModel):
    document_id: str

# -------------------------
# Upload
# -------------------------

@pdf_router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    count = await db.documents.count_documents({
        "owner": current_user["_id"],
        "source": "upload",
    })
    if count >= 3:
        raise HTTPException(403, "Upload limit reached")

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    path = os.path.join(UPLOAD_DIR, filename)

    async with aiofiles.open(path, "wb") as f:
        await f.write(await file.read())

    document = await create_uploaded_document(
        filename=file.filename,
        path=path,
        user_id=current_user["_id"],
    )

    await extract_and_index_pdf(document)

    return {"document_id": str(document["_id"]), "status": "uploaded"}

# -------------------------
# Ask (Q&A)
# -------------------------

@pdf_router.post("/ask")
async def ask_pdf(
    payload: AskRequest,
    current_user=Depends(get_current_user),
):
    document = await db.documents.find_one({
        "_id": ObjectId(payload.document_id)
    })
    if not document:
        raise HTTPException(404, "Document not found")

    chunks = semantic_search(
        query=payload.query,
        n_results=max(payload.n_results, 8),
        metadata_id=payload.document_id,
        user_id=document.get("owner"),
    )

    if not chunks:
        return {"answer": "No relevant information found."}

    valid_chunks = [
        c for c in chunks if getattr(c, "page_content", None)
    ]

    if not valid_chunks:
        return {"answer": "No readable content found."}

    context = "\n\n".join(
        c.page_content for c in valid_chunks
    )[:3500]

    prompt = f"""
Answer ONLY using the context below.

Context:
{context}

Question:
{payload.query}

Answer:
""".strip()

    return {"answer": answer_from_context(prompt)}

# -------------------------
# Summarize
# -------------------------

@pdf_router.post("/summarize")
async def summarize_pdf(
    payload: SummarizeRequest,
    current_user=Depends(get_current_user),
):
    chunks = semantic_search(
        query="summary",
        n_results=50,
        metadata_id=payload.document_id,
    )

    if not chunks:
        return {"summary": "No content found."}

    valid_chunks = [
        c for c in chunks if getattr(c, "page_content", None)
    ]

    if not valid_chunks:
        return {"summary": "No readable content found."}

    text = "\n\n".join(
        c.page_content for c in valid_chunks
    )[:4000]

    return {"summary": summarize_text(text)}
