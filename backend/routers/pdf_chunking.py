import os
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.logger import logger
from starlette.status import HTTP_201_CREATED
from bson import ObjectId
from typing import Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from backend.app.auth import get_current_user
from backend.app.db import db
from backend.app.chroma_store import add_chunks_to_chroma, semantic_search
from backend.app.llm_inference import (
    generate_answer,
    generate_summary,
    generate_followup_questions,
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

    try:
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        with open(file_location, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Error while saving uploaded file: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while saving the file."
        )

    file_doc = {
        "user_id": current_user["_id"],
        "user_email": current_user.get("email", "unknown"),
        "filename": original_filename,
        "stored_filename": safe_filename,
        "path": file_location,
        "uploaded_at": datetime.utcnow(),
        "size_bytes": len(content),
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


@pdf_router.get("/ask")
async def ask_pdf(
    query: str = Query(..., min_length=3),
    n_results: int = Query(5, ge=1, le=10),
    current_user: dict = Depends(get_current_user),
):
    chunks = semantic_search(query, n_results)
    if not chunks:
        raise HTTPException(status_code=404, detail="No relevant documents found.")

    context = "\n\n".join([chunk.page_content for chunk in chunks])
    prompt = (
        f"Answer the question based only on the following context:\n\n"
        f"{context}\n\n"
        f"Question: {query}\n"
        f"Answer:"
    )
    answer = generate_answer(prompt)
    return {"answer": answer}


@pdf_router.post("/summarize")
async def summarize_text(
    text: str = Body(..., embed=True),
    style: str = Query("paragraph", enum=["paragraph", "bullet_points"]),
):
    if style == "paragraph":
        prompt = (
            f"Summarize the following text into a concise paragraph:\n\n{text}"
        )
    else:
        prompt = (
            f"Summarize the following text into bullet points:\n\n{text}"
        )
    summary = generate_summary(prompt)
    return {"summary": summary}


@pdf_router.post("/chat")
async def chat_with_followup(
    question: str = Body(..., embed=True),
    n_results: int = Query(5, ge=1, le=10),
    previous_answer: Optional[str] = Body(None),
    current_user: dict = Depends(get_current_user),
):
    chunks = semantic_search(question, n_results)
    if not chunks:
        raise HTTPException(status_code=404, detail="No relevant documents found.")

    context = "\n\n".join([chunk.page_content for chunk in chunks])

    prompt_answer = (
        f"Answer the question based only on the following context:\n\n"
        f"{context}\n\n"
        f"Question: {question}\nAnswer:"
    )
    answer = generate_answer(prompt_answer)

    followups = []
    if previous_answer is None:
        prompt_followups = (
            f"Based on the question:\n{question}\n"
            f"and the answer:\n{answer}\n"
            f"Generate 3 relevant and natural follow-up questions a user might ask next:"
        )
        followup_text = generate_followup_questions(prompt_followups)
        followups = [
            q.strip("-. \n\t") for q in followup_text.split("\n") if q.strip()
        ][:3]

    return {
        "answer": answer,
        "follow_up_questions": followups,
    }
