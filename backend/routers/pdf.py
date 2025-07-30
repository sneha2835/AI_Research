import os
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.auth import get_current_user
from app.db import db

pdf_router = APIRouter(prefix="/pdf", tags=["PDF"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "pdf_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@pdf_router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    safe_filename = f"{current_user['_id']}_{int(datetime.utcnow().timestamp())}_{file.filename}"
    file_location = os.path.join(UPLOAD_DIR, safe_filename)

    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)

    file_doc = {
        "user_id": current_user["_id"],
        "user_email": current_user["email"],
        "filename": file.filename,
        "stored_filename": safe_filename,
        "path": file_location,
        "uploaded_at": datetime.utcnow(),
    }
    result = await db.pdf_files.insert_one(file_doc)

    return JSONResponse(
        content={
            "message": "Upload successful.",
            "filename": file.filename,
            "stored_filename": safe_filename,
            "metadata_id": str(result.inserted_id),
        }
    )
