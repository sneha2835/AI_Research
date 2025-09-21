from fastapi import APIRouter, Depends, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException, status
from backend.app.auth import get_current_user, verify_password, create_access_token
from backend.app.utils import UserRead
from backend.app.db import db

auth_router = APIRouter(tags=["Authentication"])

@auth_router.post("/register", response_model=UserRead, summary="Register a new user")
async def register(user: dict = Body(...)):
    # call your existing create_user logic
    # simplified for example
    hashed_password = "hashed_password_here"
    user["_id"] = "user_id_here"
    user.pop("password", None)
    return UserRead(**user)


@auth_router.post("/token", summary="Login for access token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # call your existing login_user logic
    return {"access_token": "token_here", "token_type": "bearer"}


@auth_router.get("/users/me", response_model=UserRead, summary="Get current user info")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return UserRead(**current_user)
