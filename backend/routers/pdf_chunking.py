# backend/routers/pdf_chunking.py

import os
import uuid
import aiofiles
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from bson import ObjectId
from pydantic import BaseModel

from backend.app.auth import get_current_user
from backend.app.db import db
from backend.app.chroma_store import semantic_search
from backend.app.llm_inference import answer_from_context
from backend.services.document_service import create_uploaded_document
from backend.services.pdf_service import extract_and_index_pdf

pdf_router = APIRouter(prefix="/pdf", tags=["PDF"])

UPLOAD_DIR = "backend/pdf_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class AskRequest(BaseModel):
    document_id: str
    query: str
    n_results: int = 5


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

    data = await file.read()
    async with aiofiles.open(path, "wb") as f:
        await f.write(data)

    document = await create_uploaded_document(
        filename=file.filename,
        path=path,
        user_id=current_user["_id"],
    )

    await extract_and_index_pdf(document)

    return {"document_id": str(document["_id"])}


@pdf_router.post("/ask")
async def ask_pdf(
    payload: AskRequest,
    current_user=Depends(get_current_user),
):
    chunks = semantic_search(
        query=payload.query,
        n_results=max(payload.n_results, 8),
        metadata_id=payload.document_id,
    )

    context = "\n\n".join(c.page_content for c in chunks)[:3500]

    prompt = f"""
Answer ONLY using the context below.

Context:
{context}

Question:
{payload.query}

Answer:
""".strip()

    return {"answer": answer_from_context(prompt)}
