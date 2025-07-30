import os
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse
from fastapi.logger import logger
from starlette.status import HTTP_201_CREATED
from bson import ObjectId

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.auth import get_current_user
from app.db import db

pdf_router = APIRouter(prefix="/pdf", tags=["PDF"])

# Directory for file storage
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pdf_uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB

def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    return "".join(c for c in filename if c.isalnum() or c in (" ", ".", "_", "-")).strip()

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
        with open(file_location, "wb") as f:
            content = await file.read()
            if len(content) > MAX_UPLOAD_SIZE:
                raise HTTPException(status_code=413, detail="File too large")
            f.write(content)
    except Exception as e:
        logger.error(f"Error while saving uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while saving the file.")

    file_doc = {
        "user_id": current_user["_id"],
        "user_email": current_user["email"],
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
        raise HTTPException(status_code=500, detail="Internal server error while saving metadata.")

    logger.info(f"User {current_user['email']} uploaded file {original_filename} saved as {safe_filename}")

    return JSONResponse(
        status_code=HTTP_201_CREATED,
        content={
            "message": "Upload successful.",
            "filename": original_filename,
            "stored_filename": safe_filename,
            "metadata_id": str(result.inserted_id),
            "size_bytes": len(content),
        }
    )

# 1. List user’s uploads
@pdf_router.get("/my_uploads")
async def list_my_uploads(current_user: dict = Depends(get_current_user)):
    cursor = db.pdf_files.find({"user_id": current_user["_id"]})
    files = []
    async for file in cursor:
        file["_id"] = str(file["_id"])
        files.append({
            "metadata_id": file["_id"],
            "filename": file["filename"],
            "stored_filename": file["stored_filename"],
            "uploaded_at": file["uploaded_at"],
            "size_bytes": file.get("size_bytes", None)
        })
    return {"files": files}

# 2. Download a PDF file (user can only access their own)
@pdf_router.get("/download/{metadata_id}")
async def download_pdf(metadata_id: str, current_user: dict = Depends(get_current_user)):
    file_doc = await db.pdf_files.find_one({"_id": ObjectId(metadata_id), "user_id": current_user["_id"]})
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found or access denied")
    file_path = file_doc["path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    return FileResponse(
        path=file_path,
        filename=file_doc["filename"],
        media_type='application/pdf'
    )

# 3. Delete a PDF file (user can only delete their own)
@pdf_router.delete("/delete/{metadata_id}")
async def delete_pdf(metadata_id: str, current_user: dict = Depends(get_current_user)):
    file_doc = await db.pdf_files.find_one({"_id": ObjectId(metadata_id), "user_id": current_user["_id"]})
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found or access denied")
    file_path = file_doc["path"]
    await db.pdf_files.delete_one({"_id": ObjectId(metadata_id)})
    if os.path.exists(file_path):
        os.remove(file_path)
    return {"message": "File deleted successfully."}

# 4. Extract and chunk PDF (PyPDFLoader) for user's file
@pdf_router.get("/extract_chunks/{metadata_id}")
async def extract_pdf_chunks(
    metadata_id: str,
    current_user: dict = Depends(get_current_user)
):
    file_doc = await db.pdf_files.find_one({"_id": ObjectId(metadata_id), "user_id": current_user["_id"]})
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found or access denied")
    file_path = file_doc["path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File missing on server")

    # Load and split with PyPDFLoader
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

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
        "chunks": chunk_results
    })
