import os
import asyncio
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from jose import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from app.db import db

load_dotenv()

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL")
JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"


# --------------------------------------------------
# 🔐 Step 1: Redirect to Google
# --------------------------------------------------

@router.get("/auth/google/login")
async def google_login():
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    return RedirectResponse(url)


# --------------------------------------------------
# 🔐 Step 2: Google Callback
# --------------------------------------------------

@router.get("/auth/google/callback")
async def google_callback(code: str):
    try:
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )

        token_data = token_response.json()

        if "id_token" not in token_data:
            raise HTTPException(status_code=400, detail="Invalid Google response")

        # 🔥 Run blocking Google verification in thread executor
        loop = asyncio.get_event_loop()
        id_info = await loop.run_in_executor(
        None,
        lambda: id_token.verify_oauth2_token(
        token_data["id_token"],
        google_requests.Request(),
        GOOGLE_CLIENT_ID,
        clock_skew_in_seconds=10,  # 👈 add this
    ),
)

        # Ensure email verified
        if not id_info.get("email_verified"):
            raise HTTPException(status_code=400, detail="Google email not verified")

        email = id_info["email"]
        name = id_info.get("name", "")

        # Check if user exists
        existing_user = await db.users.find_one({"email": email})

        if not existing_user:
            await db.users.insert_one({
        "email": email,
        "name": name,
        "provider": "google",
        "is_verified": True,
        "hashed_password": None,
    })

        # Create JWT
        from app.auth import create_access_token

        token = create_access_token(
            email=email,
            user_id=str(existing_user["_id"]) if existing_user else str(
                (await db.users.find_one({"email": email}))["_id"]
            ),
        )

        return RedirectResponse(f"{FRONTEND_URL}/oauth-success?token={token}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))