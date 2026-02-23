from fastapi import APIRouter, Depends, Body, HTTPException
from bson import ObjectId
from datetime import datetime
from typing import List

from app.auth import get_current_user, get_password_hash, verify_password
from app.db import db
from app.utils import UserRead

users_router = APIRouter(prefix="/users", tags=["Users"])


# ==================================================
# 👤 GET MY PROFILE
# ==================================================

@users_router.get("/me", response_model=UserRead)
async def get_my_profile(current_user: dict = Depends(get_current_user)):

    user_id = ObjectId(current_user["_id"])

    user = await db.users.find_one({"_id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user["_id"] = str(user["_id"])
    user.pop("password", None)

    return user


# ==================================================
# ✏️ UPDATE PROFILE (Name, Birthday, Theme)
# ==================================================

@users_router.put("/me")
async def update_profile(
    payload: dict = Body(...),
    current_user: dict = Depends(get_current_user),
):

    update_fields = {}

    # Validate Name
    if "name" in payload:
        if not payload["name"].strip():
            raise HTTPException(status_code=400, detail="Name cannot be empty")
        update_fields["name"] = payload["name"].strip()

    # Birthday
    if "birthday" in payload:
        update_fields["birthday"] = payload["birthday"]

    # Theme
    if "theme" in payload:
        if payload["theme"] not in ["light", "dark"]:
            raise HTTPException(status_code=400, detail="Theme must be 'light' or 'dark'")
        update_fields["theme"] = payload["theme"]

    if not update_fields:
        raise HTTPException(status_code=400, detail="No valid fields provided")

    user_id = ObjectId(current_user["_id"])  # 🔥 critical fix

    result = await db.users.update_one(
        {"_id": user_id},
        {"$set": update_fields}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Profile update failed")

    updated_user = await db.users.find_one({"_id": user_id})

    updated_user["_id"] = str(updated_user["_id"])
    updated_user.pop("password", None)

    return {
        "message": "Profile updated successfully",
        "user": updated_user
    }


# ==================================================
# 🔐 CHANGE PASSWORD
# ==================================================

@users_router.put("/change-password")
async def change_password(
    payload: dict = Body(...),
    current_user: dict = Depends(get_current_user),
):

    old_password = payload.get("old_password")
    new_password = payload.get("new_password")

    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="Old and new passwords are required")

    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    user_id = ObjectId(current_user["_id"])

    user = await db.users.find_one({"_id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(old_password, user["password"]):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    hashed_password = get_password_hash(new_password)

    await db.users.update_one(
        {"_id": user_id},
        {"$set": {"password": hashed_password}}
    )

    return {"message": "Password changed successfully"}


# ==================================================
# 🗑️ DELETE MY ACCOUNT
# ==================================================

@users_router.delete("/me")
async def delete_my_account(current_user: dict = Depends(get_current_user)):

    user_id = ObjectId(current_user["_id"])

    await db.users.delete_one({"_id": user_id})
    await db.documents.delete_many({"owner": user_id})
    await db.chat_history.delete_many({"user_id": user_id})
    await db.recent_views.delete_many({"user_id": user_id})

    return {"message": "Account deleted successfully"}


# ==================================================
# 📦 EXPORT CHAT HISTORY
# ==================================================

@users_router.get("/export-history")
async def export_chat_history(current_user: dict = Depends(get_current_user)):

    user_id = ObjectId(current_user["_id"])

    chats = await db.chat_history.find(
        {"user_id": user_id}
    ).sort("timestamp", 1).to_list(5000)

    export_data = []

    for chat in chats:
        export_data.append({
            "document_id": str(chat["document_id"]),
            "role": chat["role"],
            "type": chat["type"],
            "content": chat["content"],
            "timestamp": chat["timestamp"].isoformat() if chat.get("timestamp") else None
        })

    return {
        "exported_at": datetime.utcnow().isoformat(),
        "total_messages": len(export_data),
        "messages": export_data
    }