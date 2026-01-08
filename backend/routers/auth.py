# backend/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from bson import ObjectId

from backend.app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
)
from backend.app.db import db
from backend.app.utils import UserRegister, UserRead

auth_router = APIRouter(tags=["Authentication"])


@auth_router.post("/register", response_model=UserRead, status_code=201)
async def register(user: UserRegister):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)

    user_doc = {
        "name": user.name,
        "email": user.email,
        "password": hashed_password,
    }

    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = str(result.inserted_id)
    user_doc.pop("password")

    return UserRead(**user_doc)


@auth_router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    access_token = create_access_token(
        email=user["email"],
        user_id=str(user["_id"]),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@auth_router.get("/users/me", response_model=UserRead)
async def read_me(current_user=Depends(get_current_user)):
    return current_user
