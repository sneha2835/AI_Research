import os
import uuid
import aiofiles
from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends,
    Query,
    Body,
)
from fastapi.responses import JSONResponse, FileResponse
from fastapi.logger import logger
from starlette.status import HTTP_201_CREATED
from bson import ObjectId

from PyPDF2 import PdfReader

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from backend.app.auth import get_current_user
from backend.app.db import db
from backend.app.chroma_store import add_chunks_to_chroma, semantic_search
from backend.app.llm_inference import (
    answer_from_context,
    summarize_text as llm_summarize,
)

from pydantic import BaseModel

class AskRequest(BaseModel):
    metadata_id: str
    query: str
    conversation_history: Optional[str] = ""
    n_results: int = 5


class ChatMessage(BaseModel):
    metadata_id: str
    role: str
    content: str

# ------------------------------------------------------------------
# Router setup
# ------------------------------------------------------------------

pdf_router = APIRouter(prefix="/pdf", tags=["PDF"])

UPLOAD_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "pdf_uploads")
)
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
ENABLE_CHROMA = True


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    return "".join(
        c for c in filename if c.isalnum() or c in (" ", ".", "_", "-")
    ).strip()


# ------------------------------------------------------------------
# Upload PDF
# ------------------------------------------------------------------

@pdf_router.post("/upload", status_code=HTTP_201_CREATED)
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    original_filename = sanitize_filename(file.filename)
    if not original_filename:
        raise HTTPException(status_code=400, detail="Invalid file name.")

    unique_prefix = uuid.uuid4().hex
    safe_filename = f"{unique_prefix}_{original_filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large.")

    try:
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
    except Exception as e:
        logger.error(f"File save failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file.")

    # Extract page count
    try:
        with open(file_path, "rb") as f:
            reader = PdfReader(f)
            page_count = len(reader.pages)
    except Exception:
        page_count = None

    file_doc = {
        "user_id": current_user["_id"],
        "user_email": current_user.get("email"),
        "filename": original_filename,
        "stored_filename": safe_filename,
        "path": file_path,
        "uploaded_at": datetime.utcnow(),
        "size_bytes": len(content),
        "page_count": page_count,
    }

    result = await db.pdf_files.insert_one(file_doc)

    return {
        "message": "Upload successful",
        "metadata_id": str(result.inserted_id),
        "filename": original_filename,
        "page_count": page_count,
        "size_bytes": len(content),
    }


# ------------------------------------------------------------------
# List uploads
# ------------------------------------------------------------------

@pdf_router.get("/my_uploads")
async def list_my_uploads(current_user: dict = Depends(get_current_user)):
    cursor = db.pdf_files.find({"user_id": current_user["_id"]})
    files = []

    async for doc in cursor:
        files.append(
            {
                "metadata_id": str(doc["_id"]),
                "filename": doc["filename"],
                "uploaded_at": doc["uploaded_at"],
                "size_bytes": doc.get("size_bytes"),
            }
        )

    return {"files": files}


# ------------------------------------------------------------------
# Download PDF
# ------------------------------------------------------------------

@pdf_router.get("/download/{metadata_id}")
async def download_pdf(
    metadata_id: str,
    current_user: dict = Depends(get_current_user),
):
    file_doc = await db.pdf_files.find_one(
        {"_id": ObjectId(metadata_id), "user_id": current_user["_id"]}
    )
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found.")

    if not os.path.exists(file_doc["path"]):
        raise HTTPException(status_code=404, detail="File missing on server.")

    return FileResponse(
        path=file_doc["path"],
        filename=file_doc["filename"],
        media_type="application/pdf",
    )


# ------------------------------------------------------------------
# Delete PDF
# ------------------------------------------------------------------

@pdf_router.delete("/delete/{metadata_id}")
async def delete_pdf(
    metadata_id: str,
    current_user: dict = Depends(get_current_user),
):
    file_doc = await db.pdf_files.find_one(
        {"_id": ObjectId(metadata_id), "user_id": current_user["_id"]}
    )
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found.")

    await db.pdf_files.delete_one({"_id": ObjectId(metadata_id)})

    if os.path.exists(file_doc["path"]):
        os.remove(file_doc["path"])

    return {"message": "File deleted successfully."}


# ------------------------------------------------------------------
# Extract & index chunks
# ------------------------------------------------------------------

@pdf_router.get("/extract_chunks/{metadata_id}")
async def extract_pdf_chunks(
    metadata_id: str,
    current_user: dict = Depends(get_current_user),
):
    file_doc = await db.pdf_files.find_one(
        {"_id": ObjectId(metadata_id), "user_id": current_user["_id"]}
    )
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found.")

    # ✅ check FIRST
    existing = await db.chunks.find_one({"metadata_id": metadata_id})
    if existing:
        return {"status": "already_processed"}

    file_path = file_doc["path"]
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
    )
    chunks = splitter.split_documents(docs)

    if ENABLE_CHROMA:
        add_chunks_to_chroma(chunks, metadata_id)

    await db.chunks.insert_one({
        "metadata_id": metadata_id,
        "user_id": current_user["_id"],
        "created_at": datetime.utcnow(),
        "chunk_count": len(chunks)
    })

    return {
        "file": file_doc["filename"],
        "total_chunks": len(chunks),
    }


# ------------------------------------------------------------------
# Semantic search
# ------------------------------------------------------------------

@pdf_router.get("/search")
async def search_pdf_chunks(
    query: str = Query(..., min_length=3),
    n_results: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(get_current_user),
):
    results = semantic_search(query, n_results)
    return {"query": query, "results": results}


# ------------------------------------------------------------------
# Ask question (RAG – NO hallucination)
# ------------------------------------------------------------------

@pdf_router.post("/ask")
async def ask_pdf(
    payload: AskRequest,
    current_user: dict = Depends(get_current_user),
):
    chunks = semantic_search(
        payload.query,
        payload.n_results,
        metadata_id=payload.metadata_id   # 🔥 IMPORTANT
    )

    if not chunks:
        return {"answer": "I could not find this information in the document."}

    context = "\n\n".join(c.page_content for c in chunks)

    full_context = f"""
Conversation so far:
{payload.conversation_history}

Document context:
{context}
""".strip()

    answer = answer_from_context(full_context, payload.query)
    return {"answer": answer}


# ------------------------------------------------------------------
# Summarize arbitrary text
# ------------------------------------------------------------------

@pdf_router.post("/summarize")
async def summarize_text_endpoint(
    text: str = Body(..., embed=True),
):
    summary = llm_summarize(text)
    return {"summary": summary}

@pdf_router.post("/chat/save")
async def save_chat_message(
    msg: ChatMessage,
    current_user: dict = Depends(get_current_user),
):
    await db.chat_history.insert_one({
        "metadata_id": msg.metadata_id,
        "user_id": current_user["_id"],
        "role": msg.role,
        "content": msg.content,
        "timestamp": datetime.utcnow()
    })
    return {"status": "saved"}

@pdf_router.get("/chat/history/{metadata_id}")
async def get_chat_history(
    metadata_id: str,
    current_user: dict = Depends(get_current_user),
):
    cursor = db.chat_history.find(
        {"metadata_id": metadata_id, "user_id": current_user["_id"]}
    ).sort("timestamp", 1)

    messages = []
    async for doc in cursor:
        messages.append({
            "role": doc["role"],
            "content": doc["content"]
        })

    return {"messages": messages}

@pdf_router.delete("/chat/history/{metadata_id}")
async def clear_chat_history(
    metadata_id: str,
    current_user: dict = Depends(get_current_user),
):
    await db.chat_history.delete_many({
        "metadata_id": metadata_id,
        "user_id": current_user["_id"]
    })
    return {"status": "cleared"}
