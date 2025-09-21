from fastapi import APIRouter, Depends, Body, Path, Query, HTTPException
from bson import ObjectId
from typing import List
from backend.app.auth import get_current_user, get_password_hash
from backend.app.db import db
from backend.app.utils import UserRead, UserRegister

users_router = APIRouter(tags=["Users"])

@users_router.get("/users", response_model=List[UserRead], summary="List all users")
async def get_users():
    pass  # your existing logic

@users_router.put("/users/{user_id}", response_model=UserRead, summary="Update a user")
async def update_user():
    pass  # your existing logic

@users_router.delete("/users/{user_id}", summary="Delete a user")
async def delete_user():
    pass  # your existing logic

@users_router.get("/test-db", summary="Test DB connection")
async def test_db():
    count = await db.users.count_documents({})
    return {"user_count": count}
