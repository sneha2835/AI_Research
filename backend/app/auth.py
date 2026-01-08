# backend/app/auth.py

from datetime import datetime, timedelta
from typing import Optional, Dict

from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId

from backend.app.config import settings
from backend.app.db import db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# -------------------------
# Password helpers
# -------------------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    return pwd_context.hash(password)


# -------------------------
# JWT helpers
# -------------------------

def create_access_token(
    *,
    email: str,
    user_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": email,
        "uid": user_id,  # stored as string
        "iat": now,
        "exp": now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
        "type": "access",
    }

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


# -------------------------
# Current user dependency
# -------------------------

async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(security),
) -> Dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token.credentials)
        email: str | None = payload.get("sub")
        uid: str | None = payload.get("uid")

        if not email or not uid:
            raise credentials_exception

        if not ObjectId.is_valid(uid):
            raise credentials_exception

        user_id = ObjectId(uid)

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise credentials_exception

    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise credentials_exception

    user["_id"] = str(user["_id"])
    user.pop("password", None)
    return user
