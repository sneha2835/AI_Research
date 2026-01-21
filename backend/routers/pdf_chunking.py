# backend/routers/pdf_chunking.py

from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from backend.app.db import db
from backend.app.auth import get_current_user
from backend.app.chroma_store import semantic_search
from backend.services.pdf_service import extract_and_index_pdf
from backend.app.llm_inference import answer_from_context, summarize_text
from backend.schemas.pdf import AskPdfRequest, SummarizePdfRequest

import os
import re

pdf_router = APIRouter(prefix="/pdf", tags=["PDF"])

UPLOAD_DIR = "backend/pdf_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==================================================
# 🔧 HELPER FUNCTIONS
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

    document = {
    "owner": current_user["_id"],
    "title": file.filename,
    "created_at": datetime.utcnow(),
    "path": None,
    "source": "upload",
    "indexed": False, 
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

    if not document.get("indexed"):
        await extract_and_index_pdf({
            "_id": document["_id"],
            "path": path,
            "owner": current_user["_id"],
        })


    return {
        "document_id": str(document["_id"]),
        "status": "uploaded",
    }


# ==================================================
# ❓ Ask PDF (Q&A) + CHAT HISTORY
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
        raise HTTPException(status_code=404, detail="Document not found")

    source = "arxiv" if document.get("source") == "arxiv" else "upload"

    # 🕘 LOG RECENT VIEW (UPLOAD ONLY)
    if source == "upload":
        await db.recent_views.update_one(
            {
                "user_id": current_user["_id"],
                "type": "upload",
                "document_id": payload.document_id,
            },
            {
                "$set": {
                    "title": document.get("title"),
                    "viewed_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )

    chunks = semantic_search(
        query=payload.query,
        n_results=payload.n_results,
        metadata_id=payload.document_id,
        user_id=document.get("owner"),
        section_priority=True,
    )

    valid_chunks = [
        c for c in chunks
        if getattr(c, "page_content", "").strip()
        and not is_junk_chunk(c.page_content)
    ]

    valid_chunks = deduplicate_chunks(valid_chunks, payload.n_results)

    if not valid_chunks:
        answer = "No relevant content found in this document."
    else:
        context = "\n\n".join(c.page_content for c in valid_chunks)[:3500]

        prompt = f"""
You are an expert academic research assistant.

Answer the question strictly using the context below.
If the answer is not explicitly stated, say:
"The paper does not explicitly state this."

Context:
{context}

Question:
{payload.query}

Answer in clear academic English (4–6 sentences):
""".strip()

        answer = answer_from_context(prompt) or "The paper does not explicitly state this."

    # ==================================================
    # 💾 SAVE CHAT HISTORY (USER + ASSISTANT)
    # ==================================================

    timestamp = datetime.utcnow()

    await db.chat_history.insert_many([
    {
        "document_id": ObjectId(payload.document_id),
        "document_id_str": payload.document_id,
        "user_id": current_user["_id"],
        "role": "user",
        "type": "qa",
        "content": payload.query,
        "source": source,
        "timestamp": timestamp,
    },
    {
        "document_id": ObjectId(payload.document_id),
        "document_id_str": payload.document_id,
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
    # 1) Validate document access
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
        raise HTTPException(status_code=404, detail="Document not found")
    
    source = "arxiv" if document.get("source") == "arxiv" else "upload"

    # ==================================================
    # 🕘 LOG RECENT VIEW (UPLOAD ONLY)
    # ==================================================
    if source == "upload":
        await db.recent_views.update_one(
            {
                "user_id": current_user["_id"],
                "type": "upload",
                "document_id": payload.document_id,
            },
            {
                "$set": {
                    "title": document.get("title"),
                    "viewed_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )

        
    # 2) Retrieve chunks
    chunks = semantic_search(
        query="Summarize the main contributions and findings of this paper",
        n_results=12,
        metadata_id=payload.document_id,
        user_id=document.get("owner"),
        section_priority=True,
    )

    valid_chunks = [
        c for c in chunks
        if getattr(c, "page_content", "").strip()
        and not is_junk_chunk(c.page_content)
    ]

    valid_chunks = deduplicate_chunks(valid_chunks, 10)

    if not valid_chunks:
        return {"summary": "No readable content found in this document."}

    # 3) Build context
    context = "\n\n".join(c.page_content for c in valid_chunks)[:4000]

    # 4) Structured summarization prompt
    prompt = f"""
Summarize the following academic paper using the structure below.

Format:
Objective:
Problem Statement:
Methodology (if mentioned):
Key Findings:
Conclusion:

Text:
{context}
""".strip()

    summary = summarize_text(prompt)

    if not summary or not summary.strip():
        summary = (
            "Objective:\nNot clearly stated.\n\n"
            "Problem Statement:\nNot clearly stated.\n\n"
            "Methodology:\nNot clearly stated.\n\n"
            "Key Findings:\nNot clearly stated.\n\n"
            "Conclusion:\nNot clearly stated."
        )
    # ==================================================
    # 💾 SAVE SUMMARY TO CHAT HISTORY
    # ==================================================

    source = "arxiv" if document.get("source") == "arxiv" else "upload"

    await db.chat_history.insert_one({
    "document_id": ObjectId(payload.document_id),
    "document_id_str": payload.document_id,
    "user_id": current_user["_id"],
    "role": "assistant",
    "type": "summary",
    "content": summary,
    "source": source,
    "timestamp": datetime.utcnow(),
})


    return {"summary": summary}

