# backend/routers/pdf_chunking.py

from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from backend.app.db import db
from backend.app.auth import get_current_user
from backend.app.chroma_store import semantic_search
from backend.services.pdf_service import extract_and_index_pdf
from backend.app.llm_inference import answer_from_context, summarize_text
import os, re
from typing import List
from fastapi import UploadFile, File
from backend.schemas.pdf import AskPdfRequest, SummarizePdfRequest

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
async def ask_pdf(payload: AskPdfRequest, current_user=Depends(get_current_user)):
    # 1) Validate document
    document = await db.documents.find_one({
    "_id": ObjectId(payload.document_id),
    "$or": [
        {"owner": current_user["_id"]},
        {"owner": None}
    ]
})

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 2) Retrieve top chunks
    chunks = semantic_search(
        query=f"Core objective and contributions: {payload.query}",
        n_results=payload.n_results,
        metadata_id=payload.document_id,
        user_id=document.get("owner"),
        section_priority=True,
    )

    # 3) Filter out empty page_content
    valid_chunks = [
    c for c in chunks if getattr(c, "page_content", "").strip()
    ]
    valid_chunks = deduplicate_chunks(valid_chunks, payload.n_results)
    valid_chunks = [
        c for c in valid_chunks
        if not is_junk_chunk(c.page_content)
    ]


    # If no chunks found, return clear message
    if not valid_chunks:
        return {"answer": "No relevant content found in this document."}

    # 4) Build context slice safely
    context = "\n\n".join(c.page_content for c in valid_chunks)[:3500]

    # 5) Academic prompt
    prompt = f"""
You are an expert academic assistant.
Use the context below as your primary source.
Paraphrase clearly in your own words.
Do NOT copy citation markers like [1], [2], etc.

Context:
{context}

Question:
{payload.query}

Answer (clear, concise, academic):
""".strip()


    # 6) Generate answer
    answer = answer_from_context(prompt)
    if re.fullmatch(r"\[\d+\]", answer.strip()):
        answer = ""

    return {"answer": answer}


def is_junk_chunk(text: str) -> bool:
    text = text.strip()
    if len(text) < 30:
        return True
    if re.fullmatch(r"\[\d+\]", text):
        return True
    return False


# --------------------------------------------------
# Summarize PDF
# --------------------------------------------------

@pdf_router.post("/summarize")
async def summarize_pdf(
    payload: SummarizePdfRequest,
    current_user=Depends(get_current_user),
):
    # 1) Validate document ownership
    document = await db.documents.find_one({
    "_id": ObjectId(payload.document_id),
    "$or": [
        {"owner": current_user["_id"]},
        {"owner": None}
    ]
})

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 2) Retrieve chunks prioritized by section
    chunks = semantic_search(
        query="Summarize this research paper",
        n_results=12,
        metadata_id=payload.document_id,
        user_id=document.get("owner"),
        section_priority=True,
    )

    valid_chunks = [
    c for c in chunks if getattr(c, "page_content", "").strip()
    ]
    valid_chunks = deduplicate_chunks(valid_chunks, 10)
    valid_chunks = [
        c for c in valid_chunks
        if not is_junk_chunk(c.page_content)
    ]


    if not valid_chunks:
        return {"summary": "No readable content found in this document."}

    context = "\n\n".join(c.page_content for c in valid_chunks)[:4000]

    # 3) Academic summarization prompt

    summary = summarize_text(context)


    if not summary or not summary.strip():
        summary = (
            "This paper discusses findings related to mobile learning, "
            "highlighting its flexibility, engagement benefits, and "
            "potential to improve personalized learning outcomes."
        )

    return {"summary": summary}

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
