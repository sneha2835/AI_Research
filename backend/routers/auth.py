from fastapi import APIRouter, Depends, Body, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from backend.app.auth import get_current_user, verify_password, create_access_token, get_password_hash
from backend.app.utils import UserRead, UserRegister
from backend.app.db import db
from bson import ObjectId

auth_router = APIRouter(tags=["Authentication"])

@auth_router.post("/register", response_model=UserRead, status_code=201, summary="Register a new user")
async def register(user: UserRegister = Body(...)):
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
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


@auth_router.post("/token", summary="Login for access token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_doc = await db.users.find_one({"email": form_data.username})
    if not user_doc:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    if not verify_password(form_data.password, user_doc["password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(data={"sub": user_doc["email"]})
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.get("/users/me", response_model=UserRead, summary="Get current user info")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return UserRead(**current_user)
