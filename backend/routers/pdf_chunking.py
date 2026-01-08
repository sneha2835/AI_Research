# backend/routers/pdf_chunking.py

import os
import uuid
import aiofiles
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Body
from bson import ObjectId
from PyPDF2 import PdfReader

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic import BaseModel

from backend.app.auth import get_current_user
from backend.app.db import db
from backend.app.chroma_store import add_chunks_to_chroma, semantic_search, delete_pdf_chunks
from backend.app.llm_inference import answer_from_context, summarize_text

pdf_router = APIRouter(prefix="/pdf", tags=["PDF"])

UPLOAD_DIR = "backend/pdf_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class AskRequest(BaseModel):
    metadata_id: str
    query: str
    n_results: int = 5

class ChatMessage(BaseModel):
    metadata_id: str
    role: str
    content: str
    source: str

@pdf_router.post("/upload")
async def upload_pdf(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    count = await db.pdf_files.count_documents({"user_id": current_user["_id"]})
    if count >= 3:
        raise HTTPException(403, "Upload limit reached")

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    path = os.path.join(UPLOAD_DIR, filename)

    data = await file.read()
    async with aiofiles.open(path, "wb") as f:
        await f.write(data)

    reader = PdfReader(path)
    result = await db.pdf_files.insert_one({
        "user_id": current_user["_id"],
        "filename": file.filename,
        "path": path,
        "page_count": len(reader.pages),
        "source": "upload",
        "uploaded_at": datetime.utcnow(),
    })

    return {"metadata_id": str(result.inserted_id)}

@pdf_router.delete("/delete/{metadata_id}")
async def delete_pdf(metadata_id: str, current_user=Depends(get_current_user)):
    doc = await db.pdf_files.find_one({"_id": ObjectId(metadata_id), "user_id": current_user["_id"]})
    if not doc:
        raise HTTPException(404)

    delete_pdf_chunks(metadata_id)
    await db.chunks.delete_many({"metadata_id": metadata_id})
    os.remove(doc["path"])
    await db.pdf_files.delete_one({"_id": ObjectId(metadata_id)})

    return {"status": "deleted"}

@pdf_router.post("/ask")
async def ask_pdf(payload: AskRequest, current_user=Depends(get_current_user)):
    chunks = semantic_search(
        payload.query,
        n_results=max(payload.n_results, 8),
        metadata_id=payload.metadata_id,
        user_id=current_user["_id"],
    )

    if not chunks:
        return {"answer": "No relevant information found."}

    context = "\n\n".join(c.page_content for c in chunks)[:3500]

    prompt = f"""
Answer ONLY from the context below.

Context:
{context}

Question:
{payload.query}

Answer:
""".strip()

    return {"answer": answer_from_context(prompt)}

@pdf_router.post("/chat/save")
async def save_chat(msg: ChatMessage, current_user=Depends(get_current_user)):
    await db.chat_history.insert_one({
        "metadata_id": msg.metadata_id,
        "user_id": current_user["_id"],
        "role": msg.role,
        "content": msg.content,
        "source": msg.source,
        "timestamp": datetime.utcnow(),
    })
    return {"status": "saved"}
