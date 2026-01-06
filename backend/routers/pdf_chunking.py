import os
import aiofiles
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.logger import logger
from fastapi.concurrency import run_in_threadpool
from starlette.status import HTTP_201_CREATED
from bson import ObjectId
from typing import Optional
from pydantic import BaseModel

from PyPDF2 import PdfReader

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from backend.app.auth import get_current_user
from backend.app.db import db
from backend.app.chroma_store import add_chunks_to_chroma, semantic_search
from backend.app.llm_inference_groq import (
    generate_answer,
    generate_summary,
    generate_followup_questions,
    search_web,
    format_web_results,
)

pdf_router = APIRouter(prefix="/pdf", tags=["PDF"])

UPLOAD_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "pdf_uploads")
)
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_UPLOAD_SIZE = 50 * 1024 * 1024


def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    return "".join(
        c for c in filename if c.isalnum() or c in (" ", ".", "_", "-")
    ).strip()


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
    file_location = os.path.join(UPLOAD_DIR, safe_filename)

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    try:
        async with aiofiles.open(file_location, "wb") as f:
            await f.write(content)
    except Exception as e:
        logger.error(f"Error while saving uploaded file: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while saving the file."
        )

    # Extract PDF metadata (pages)
    try:
        with open(file_location, "rb") as f:
            reader = PdfReader(f)
            page_count = len(reader.pages)
    except Exception:
        page_count = None

    file_doc = {
        "user_id": current_user["_id"],
        "user_email": current_user.get("email", "unknown"),
        "filename": original_filename,
        "stored_filename": safe_filename,
        "path": file_location,
        "uploaded_at": datetime.utcnow(),
        "size_bytes": len(content),
        "page_count": page_count,
    }

    try:
        result = await db.pdf_files.insert_one(file_doc)
    except Exception as e:
        logger.error(f"Error inserting file metadata into DB: {e}")
        if os.path.exists(file_location):
            os.remove(file_location)
        raise HTTPException(
            status_code=500, detail="Internal server error while saving metadata."
        )

    return JSONResponse(
        status_code=HTTP_201_CREATED,
        content={
            "message": "Upload successful.",
            "filename": original_filename,
            "stored_filename": safe_filename,
            "metadata_id": str(result.inserted_id),
            "size_bytes": len(content),
            "page_count": page_count,
        },
    )


@pdf_router.get("/my_uploads")
async def list_my_uploads(current_user: dict = Depends(get_current_user)):
    cursor = db.pdf_files.find({"user_id": current_user["_id"]})
    files = []
    async for file in cursor:
        file["_id"] = str(file["_id"])
        files.append(
            {
                "metadata_id": file["_id"],
                "filename": file["filename"],
                "stored_filename": file["stored_filename"],
                "uploaded_at": file["uploaded_at"],
                "size_bytes": file.get("size_bytes"),
            }
        )
    return {"files": files}


@pdf_router.get("/download/{metadata_id}")
async def download_pdf(metadata_id: str, current_user: dict = Depends(get_current_user)):
    file_doc = await db.pdf_files.find_one(
        {"_id": ObjectId(metadata_id), "user_id": current_user["_id"]}
    )
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    file_path = file_doc["path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=file_path, filename=file_doc["filename"], media_type="application/pdf"
    )


@pdf_router.delete("/delete/{metadata_id}")
async def delete_pdf(metadata_id: str, current_user: dict = Depends(get_current_user)):
    file_doc = await db.pdf_files.find_one(
        {"_id": ObjectId(metadata_id), "user_id": current_user["_id"]}
    )
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    file_path = file_doc["path"]
    await db.pdf_files.delete_one({"_id": ObjectId(metadata_id)})
    if os.path.exists(file_path):
        os.remove(file_path)

    return {"message": "File deleted successfully."}


ENABLE_CHROMA = True


@pdf_router.get("/extract_chunks/{metadata_id}")
async def extract_pdf_chunks(metadata_id: str, current_user: dict = Depends(get_current_user)):
    file_doc = await db.pdf_files.find_one({
        "_id": ObjectId(metadata_id),
        "user_id": current_user["_id"]
    })
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found or access denied")

    file_path = file_doc["path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File missing on server")

    loader = PyPDFLoader(file_path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    if ENABLE_CHROMA:
        add_chunks_to_chroma(chunks, metadata_id)

    chunk_results = [
        {
            "chunk_id": idx,
            "page_number": chunk.metadata.get("page", -1),
            "text": chunk.page_content,
        }
        for idx, chunk in enumerate(chunks)
    ]

    return JSONResponse({
        "file": file_doc["filename"],
        "total_chunks": len(chunk_results),
        "chunks": chunk_results,
    })


@pdf_router.get("/search")
async def search_pdf_chunks(
    query: str = Query(..., min_length=3),
    n_results: int = Query(5, ge=1, le=20),
    current_user: dict = Depends(get_current_user),
):
    chunks = semantic_search(query, n_results)
    return {"query": query, "results": chunks}


class AskRequest(BaseModel):
    query: str
    conversation_history: str = ''
    n_results: int = 5

@pdf_router.post("/ask")
async def ask_pdf(
    request: AskRequest,
    current_user: dict = Depends(get_current_user),
):
    # Security: Input sanitization
    query = request.query[:2000]
    query = "".join(c for c in query if c.isprintable())
    
    chunks = semantic_search(query, request.n_results)
    if not chunks:
        raise HTTPException(status_code=404, detail="No relevant documents found.")

    context = "\n\n".join([chunk.page_content for chunk in chunks])
    
    # Build prompt with conversation history for memory
    if request.conversation_history:
        prompt = (
            f"You are a helpful AI assistant analyzing a document. "
            f"Here is the conversation history:\n\n{request.conversation_history}\n\n"
            f"Now, based on the following context from the document, answer the user's question:\n\n"
            f"Context: {context}\n\n"
            f"Current Question: {query}\n\n"
            f"Answer (considering the conversation history and the document context):"
        )
    else:
        prompt = (
            f"Answer the question based only on the following context:\n\n"
            f"{context}\n\n"
            f"Question: {query}\n"
            f"Answer:"
        )
    
    # Run blocking LLM call in thread pool
    answer = await run_in_threadpool(generate_answer, prompt)
    return {"answer": answer}


@pdf_router.post("/summarize")
async def summarize_text(
    text: str = Body(..., embed=True),
    style: str = Query("paragraph", enum=["paragraph", "bullet_points"]),
):
    # Security: Input sanitization
    text = text[:10000]  # Cap summary text length
    text = "".join(c for c in text if c.isprintable())
    
    if style == "paragraph":
        prompt = (
            f"Summarize the following text into a concise paragraph:\n\n{text}"
        )
    else:
        prompt = (
            f"Summarize the following text into bullet points:\n\n{text}"
        )
    
    # Run blocking LLM call in thread pool
    summary = await run_in_threadpool(generate_summary, prompt)
    return {"summary": summary}


@pdf_router.post("/chat")
async def chat_with_followup(
    question: str = Body(..., embed=True),
    n_results: int = Query(5, ge=1, le=10),
    previous_answer: Optional[str] = Body(None),
    current_user: dict = Depends(get_current_user),
):
    # Generate request ID for observability
    request_id = uuid.uuid4().hex[:8]
    logger.info(f"[{request_id}] Chat request started")
    
    # Security: Prompt injection protection
    question = question[:2000]  # Hard cap
    question = "".join(c for c in question if c.isprintable())  # Strip control chars
    
    chunks = semantic_search(question, n_results)
    if not chunks:
        raise HTTPException(status_code=404, detail="No relevant documents found.")

    context = "\n\n".join([chunk.page_content for chunk in chunks])

    # First, try to answer from the PDF context
    prompt_answer = (
        f"You are a document-only Q&A assistant. You can ONLY answer from the provided context below.\n\n"
        f"ABSOLUTE RULES:\n"
        f"1. DO NOT use your general knowledge or training data\n"
        f"2. DO NOT provide information from memory or common knowledge\n"
        f"3. ONLY look at the context provided below\n"
        f"4. If the answer IS in the context → provide a clear answer\n"
        f"5. If the answer is NOT in the context → respond with exactly: NOT_IN_DOCUMENT\n"
        f"6. Do NOT add explanations, disclaimers, or alternatives\n"
        f"7. If the context does not fully answer the question, say so explicitly\n\n"
        f"Context from PDF:\n{context}\n\n"
        f"Question: {question}\n\n"
        f"Answer (from context only, or exactly 'NOT_IN_DOCUMENT'):"
    )
    
    # Run blocking LLM call in thread pool
    answer = await run_in_threadpool(generate_answer, prompt_answer)
    
    # Strict equality check for NOT_IN_DOCUMENT detection
    if answer.strip() == "NOT_IN_DOCUMENT":
        logger.info(f"[{request_id}] Answer not in document, searching web")
        
        # Run blocking web search in thread pool
        web_results_structured = await run_in_threadpool(search_web, question)
        web_results_formatted = format_web_results(web_results_structured)
        
        # Generate answer with citation discipline
        web_prompt = (
            f"Answer the question ONLY using the web search results below.\n\n"
            f"Rules:\n"
            f"- Do NOT use your prior knowledge\n"
            f"- Cite sources inline as [1], [2], [3]\n"
            f"- If unsure or results are insufficient, say so explicitly\n"
            f"- Be concise and factual\n\n"
            f"Web Search Results:\n{web_results_formatted}\n\n"
            f"Question: {question}\n\n"
            f"Answer (cite sources):"
        )
        
        web_answer = await run_in_threadpool(generate_answer, web_prompt)
        answer = f"📄 This information was not found in the PDF document.\n\n🌐 Here's what I found on the web:\n\n{web_answer}"

    followups = []
    if previous_answer is None:
        prompt_followups = (
            f"Based on the question:\n{question}\n"
            f"and the answer:\n{answer}\n"
            f"Generate 3 relevant and natural follow-up questions a user might ask next:"
        )
        followup_text = await run_in_threadpool(generate_followup_questions, prompt_followups)
        followups = [
            q.strip("-. \n\t") for q in followup_text.split("\n") if q.strip()
        ][:3]

    logger.info(f"[{request_id}] Chat request completed")
    return {
        "answer": answer,
        "follow_up_questions": followups,
    }


# Chat History Endpoints
class ChatMessage(BaseModel):
    metadata_id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[datetime] = None


@pdf_router.post("/chat/save")
async def save_chat_message(
    message: ChatMessage,
    current_user: dict = Depends(get_current_user),
):
    """Save a single chat message to the database"""
    message_data = {
        "metadata_id": message.metadata_id,
        "user_id": current_user["_id"],
        "role": message.role,
        "content": message.content,
        "timestamp": message.timestamp or datetime.utcnow(),
    }
    
    result = await db.chat_history.insert_one(message_data)
    return {"message_id": str(result.inserted_id)}


@pdf_router.get("/chat/history/{metadata_id}")
async def get_chat_history(
    metadata_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Retrieve chat history for a specific PDF"""
    # Verify user has access to this PDF
    file_doc = await db.pdf_files.find_one({
        "_id": ObjectId(metadata_id),
        "user_id": current_user["_id"]
    })
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found or access denied")
    
    # Get chat history
    messages = await db.chat_history.find({
        "metadata_id": metadata_id,
        "user_id": current_user["_id"]
    }).sort("timestamp", 1).to_list(length=None)
    
    # Convert ObjectId to string for JSON serialization
    for msg in messages:
        msg["_id"] = str(msg["_id"])
        msg["user_id"] = str(msg["user_id"])
    
    return {"messages": messages}


@pdf_router.delete("/chat/history/{metadata_id}")
async def clear_chat_history(
    metadata_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Clear chat history for a specific PDF"""
    result = await db.chat_history.delete_many({
        "metadata_id": metadata_id,
        "user_id": current_user["_id"]
    })
    
    return {"deleted_count": result.deleted_count}
