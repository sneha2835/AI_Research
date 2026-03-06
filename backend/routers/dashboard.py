from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app.db import db
from bson import ObjectId
from datetime import datetime

dashboard_router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

# ==================================================
# 📊 DASHBOARD STATS
# ==================================================
@dashboard_router.get("/stats")
async def get_dashboard_stats(current_user=Depends(get_current_user)):

    user_id = current_user["_id"]

    # 1️⃣ Upload count (no duplicates possible)
    upload_count = await db.documents.count_documents({
        "owner": user_id,
        "source": "upload"
    })

    # 2️⃣ Unique analyzed documents (no duplicate counting)
    analyzed_documents = await db.chat_history.distinct(
        "document_id",
        {
            "user_id": user_id,
            "$or": [
                {"type": "qa"},
                {"type": "summary"}
            ]
        }
    )

    analyzed_count = len(analyzed_documents)

    # 3️⃣ Chat sessions (unique docs with QA)
    chat_documents = await db.chat_history.distinct(
        "document_id",
        {
            "user_id": user_id,
            "type": "qa"
        }
    )

    chat_count = len(chat_documents)

    # 4️⃣ Summary count (total summaries generated)
    summary_count = await db.chat_history.count_documents({
        "user_id": user_id,
        "type": "summary"
    })

    return {
        "uploads": upload_count,
        "analyzed": analyzed_count,
        "chatCount": chat_count,
        "summaryCount": summary_count
    }
# ==================================================
# 💬 CHAT SESSIONS
# ==================================================

@dashboard_router.get("/chat-sessions")
async def get_chat_sessions(current_user=Depends(get_current_user)):

    user_id = current_user["_id"]

    document_ids = await db.chat_history.distinct(
        "document_id",
        {
            "user_id": user_id,
            "type": "qa"
        }
    )

    sessions = []

    for doc_id in document_ids:
        document = await db.documents.find_one({"_id": doc_id})

        sessions.append({
            "document_id": str(doc_id),
            "title": document["title"] if document else "Untitled Document"
        })

    return sessions


# ==================================================
# 📝 SUMMARIES
# ==================================================

@dashboard_router.get("/summaries")
async def get_summaries(current_user=Depends(get_current_user)):

    user_id = current_user["_id"]

    summaries = await db.chat_history.find(
        {
            "user_id": user_id,
            "type": "summary"
        }
    ).sort("timestamp", -1).to_list(100)

    results = []

    for s in summaries:
        document = await db.documents.find_one({"_id": s["document_id"]})

        results.append({
            "summary_id": str(s["_id"]),
            "document_id": str(s["document_id"]),
            "title": document["title"] if document else "Untitled Document",
            "content": s["content"],
            "timestamp": s["timestamp"]
        })

    return results


# ==================================================
# 👤 PROFILE
# ==================================================

@dashboard_router.get("/profile")
async def get_profile(current_user=Depends(get_current_user)):

    user_id = current_user["_id"]

    upload_count = await db.documents.count_documents({
        "owner": user_id,
        "source": "upload"
    })

    summary_count = await db.chat_history.count_documents({
        "user_id": user_id,
        "type": "summary"
    })

    unique_documents = await db.chat_history.distinct(
        "document_id",
        {
            "user_id": user_id,
            "type": "qa"
        }
    )

    chat_count = len(unique_documents)

    return {
        "name": current_user.get("name"),
        "email": current_user.get("email"),
        "joined_at": current_user.get("created_at"),
        "stats": {
            "uploads": upload_count,
            "chats": chat_count,
            "summaries": summary_count
        }
    }