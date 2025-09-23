from fastapi import APIRouter, Depends, Body, Path, Query, HTTPException
from bson import ObjectId
from typing import List
from backend.app.auth import get_current_user, get_password_hash
from backend.app.db import db
from backend.app.utils import UserRead, UserRegister

users_router = APIRouter(tags=["Users"])


@users_router.get("/users", response_model=List[UserRead], summary="List all users")
async def get_users():
    users = []
    cursor = db.users.find({})
    async for user_doc in cursor:
        user_doc["_id"] = str(user_doc["_id"])
        user_doc.pop("password", None)
        users.append(user_doc)
    return users


@users_router.put("/users/{user_id}", response_model=UserRead, summary="Update a user")
async def update_user(
    user_id: str = Path(...),
    user_update: UserRegister = Body(...),
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    existing_user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = get_password_hash(user_update.password)

    update_doc = {
        "name": user_update.name,
        "email": user_update.email,
        "password": hashed_password,
    }

    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_doc})
    updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
    updated_user["_id"] = str(updated_user["_id"])
    updated_user.pop("password", None)

    return UserRead(**updated_user)


@users_router.delete("/users/{user_id}", summary="Delete a user")
async def delete_user(
    user_id: str = Path(...),
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    await db.users.delete_one({"_id": ObjectId(user_id)})

    return {"message": "User deleted successfully"}


@users_router.get("/test-db", summary="Test DB connection")
async def test_db():
    count = await db.users.count_documents({})
    return {"user_count": count}
