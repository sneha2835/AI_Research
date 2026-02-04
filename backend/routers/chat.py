from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from backend.app.db import db
from backend.app.auth import get_current_user

chat_router = APIRouter(prefix="/chat", tags=["Chat"])

# ==================================================
# 💬 Get chat history for a document
# ==================================================

@chat_router.get("/{document_id}")
async def get_chat_history(
    document_id: str,
    current_user=Depends(get_current_user),
):
    if not ObjectId.is_valid(document_id):
        raise HTTPException(status_code=400, detail="Invalid document id")

    document = await db.documents.find_one({
        "_id": ObjectId(document_id),
        "$or": [
            {"owner": current_user["_id"]},
            {"owner": None},  # arXiv papers
        ],
    })

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    chats = await db.chat_history.find(
        {
            "document_id": ObjectId(document_id),
            "user_id": current_user["_id"],
        }
    ).sort("timestamp", 1).to_list(500)

    for chat in chats:
        chat["_id"] = str(chat["_id"])
        chat["document_id"] = str(chat["document_id"])

    return {
        "document": {
            "id": str(document["_id"]),
            "title": document.get("title") or document.get("filename"),
            "source": document.get("source", "upload"),
        },
        "messages": chats,
    }
