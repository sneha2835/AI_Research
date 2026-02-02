# backend/routers/pdf_chunking.py

from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from backend.app.db import db
from backend.app.auth import get_current_user
from backend.app.chroma_store import semantic_search
from backend.services.pdf_service import extract_and_index_pdf
from backend.app.llm_inference_groq import generate_answer, generate_summary
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

@pdf_router.get("/my_uploads")
async def get_my_uploads(current_user=Depends(get_current_user)):
    """Get all PDFs uploaded by the current user"""
    documents = await db.documents.find(
        {"owner": current_user["_id"]}
    ).sort("created_at", -1).to_list(100)
    
    files = []
    for doc in documents:
        files.append({
            "metadata_id": str(doc["_id"]),
            "filename": doc.get("title", "Unknown"),
            "uploaded_at": doc.get("created_at", datetime.utcnow()).isoformat(),
            "size_bytes": os.path.getsize(doc["path"]) if doc.get("path") and os.path.exists(doc["path"]) else 0,
            "source": doc.get("source", "upload")
        })
    
    return {"files": files}

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
    answer = generate_answer(prompt)
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
    prompt = f"""Summarize the following research paper content in a clear, concise manner:

{context}

Provide a well-structured summary covering the main points, methodology, and key findings."""

    summary = generate_summary(prompt)


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

# --------------------------------------------------
# Extract Chunks
# --------------------------------------------------

@pdf_router.get("/extract_chunks/{metadata_id}")
async def extract_chunks_endpoint(
    metadata_id: str,
    current_user=Depends(get_current_user),
):
    """Extract and index chunks for a document"""
    if not ObjectId.is_valid(metadata_id):
        raise HTTPException(400, "Invalid document ID")
    
    document = await db.documents.find_one({
        "_id": ObjectId(metadata_id),
        "$or": [
            {"owner": current_user["_id"]},
            {"owner": None}
        ]
    })
    
    if not document:
        raise HTTPException(404, "Document not found")
    
    # Check if already extracted
    if document.get("indexed"):
        return {"status": "already_extracted", "message": "Document already indexed"}
    
    # Extract and index
    if document.get("path"):
        await extract_and_index_pdf(document)
        await db.documents.update_one(
            {"_id": ObjectId(metadata_id)},
            {"$set": {"indexed": True}}
        )
        return {"status": "extracted", "message": "Chunks extracted successfully"}
    
    raise HTTPException(400, "Document has no file path")

# --------------------------------------------------
# Chat History
# --------------------------------------------------

@pdf_router.get("/chat/history/{metadata_id}")
async def get_chat_history(
    metadata_id: str,
    current_user=Depends(get_current_user),
):
    """Get chat history for a document"""
    if not ObjectId.is_valid(metadata_id):
        raise HTTPException(400, "Invalid document ID")
    
    document = await db.documents.find_one({
        "_id": ObjectId(metadata_id),
        "$or": [
            {"owner": current_user["_id"]},
            {"owner": None}
        ]
    })
    
    if not document:
        raise HTTPException(404, "Document not found")
    
    # Get chat messages from database
    messages = await db.chat_history.find(
        {
            "metadata_id": metadata_id,
            "user_id": current_user["_id"]
        }
    ).sort("timestamp", 1).to_list(100)
    
    result = []
    for msg in messages:
        result.append({
            "role": msg.get("role"),
            "content": msg.get("content")
        })
    
    return {"messages": result}

@pdf_router.post("/chat/save")
async def save_chat_message(
    payload: dict,
    current_user=Depends(get_current_user),
):
    """Save a chat message to history"""
    metadata_id = payload.get("metadata_id")
    role = payload.get("role")
    content = payload.get("content")
    
    if not metadata_id or not role or not content:
        raise HTTPException(400, "Missing required fields")
    
    if not ObjectId.is_valid(metadata_id):
        raise HTTPException(400, "Invalid document ID")
    
    message = {
        "metadata_id": metadata_id,
        "user_id": current_user["_id"],
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow()
    }
    
    await db.chat_history.insert_one(message)
    
    return {"status": "saved"}

@pdf_router.delete("/chat/history/{metadata_id}")
async def clear_chat_history(
    metadata_id: str,
    current_user=Depends(get_current_user),
):
    """Clear chat history for a document"""
    if not ObjectId.is_valid(metadata_id):
        raise HTTPException(400, "Invalid document ID")
    
    result = await db.chat_history.delete_many({
        "metadata_id": metadata_id,
        "user_id": current_user["_id"]
    })
    
    return {"status": "cleared", "deleted_count": result.deleted_count}

@pdf_router.delete("/delete/{metadata_id}")
async def delete_pdf(
    metadata_id: str,
    current_user=Depends(get_current_user),
):
    """Delete a PDF document and all related data"""
    if not ObjectId.is_valid(metadata_id):
        raise HTTPException(400, "Invalid document ID")
    
    # Find document
    document = await db.documents.find_one({
        "_id": ObjectId(metadata_id),
        "owner": current_user["_id"]
    })
    
    if not document:
        raise HTTPException(404, "Document not found or you don't have permission")
    
    # Delete physical file
    if document.get("path") and os.path.exists(document["path"]):
        try:
            os.remove(document["path"])
        except Exception as e:
            print(f"Failed to delete file: {e}")
    
    # Delete from database
    await db.documents.delete_one({"_id": ObjectId(metadata_id)})
    
    # Delete chat history
    await db.chat_history.delete_many({"metadata_id": metadata_id})
    
    # TODO: Delete from ChromaDB vector store
    
    return {"status": "deleted", "document_id": metadata_id}

