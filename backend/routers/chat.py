# backend/routers/chat.py

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from bson import ObjectId
from typing import List

from backend.app.db import db
from backend.app.auth import get_current_user
from pydantic import BaseModel, Field

chat_router = APIRouter(prefix="/pdf/chat", tags=["Chat"])


# -------------------------
# Schemas
# -------------------------

class ChatMessageCreate(BaseModel):
    metadata_id: str
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatMessageRead(BaseModel):
    role: str
    content: str
    timestamp: datetime


# -------------------------
# Save chat message
# -------------------------

@chat_router.post("/save")
async def save_chat_message(
    payload: ChatMessageCreate,
    current_user=Depends(get_current_user),
):
    if not ObjectId.is_valid(payload.metadata_id):
        raise HTTPException(400, "Invalid document id")

    document = await db.documents.find_one({
        "_id": ObjectId(payload.metadata_id),
        "$or": [
            {"owner": current_user["_id"]},
            {"owner": None}
        ]
    })

    if not document:
        raise HTTPException(404, "Document not found")

    source = "arxiv" if document.get("source") == "arxiv" else "upload"

    chat_doc = {
        "document_id": payload.metadata_id,
        "user_id": current_user["_id"],
        "role": payload.role,
        "content": payload.content,
        "source": source,
        "timestamp": datetime.utcnow(),
    }

    await db.chat_history.insert_one(chat_doc)
    return {"status": "saved"}


# -------------------------
# Load chat history
# -------------------------

@chat_router.get("/history/{metadata_id}")
async def get_chat_history(
    metadata_id: str,
    limit: int = 20,
    current_user=Depends(get_current_user),
):
    if not ObjectId.is_valid(metadata_id):
        raise HTTPException(400, "Invalid document id")

    cursor = (
        db.chat_history.find({
            "document_id": ObjectId(metadata_id),
            "user_id": current_user["_id"],
        })
        .sort("timestamp", 1)
        .limit(limit)
    )

    messages = []
    async for msg in cursor:
        messages.append({
            "role": msg["role"],
            "type": msg.get("type", "qa"),
            "content": msg["content"],
            "timestamp": msg["timestamp"],
        })

    return {"messages": messages}


# -------------------------
# Clear chat history
# -------------------------

@chat_router.delete("/history/{metadata_id}")
async def clear_chat_history(
    metadata_id: str,
    current_user=Depends(get_current_user),
):
    await db.chat_history.delete_many({
        "document_id": ObjectId(metadata_id),
        "user_id": current_user["_id"],
    })
    return {"status": "cleared"}
