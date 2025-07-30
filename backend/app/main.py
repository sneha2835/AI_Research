from fastapi import FastAPI, Request, HTTPException, Body, Path, Query, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm
from pymongo.errors import DuplicateKeyError
import logging
from typing import List
from bson import ObjectId

from routers.pdf import pdf_router  # Ensure PYTHONPATH includes parent folder of 'backend'
from .db import db
from .utils import UserRegister, UserRead  # UserRegister for registration/login data, UserRead for output
from .auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    get_current_user,
)

app = FastAPI()

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# CORS Middleware - adjust allow_origins for production to frontend URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()  # This line is just for clarity; not directly used here, used inside auth.py

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code} for {request.method} {request.url}")
    return response


@app.on_event("startup")
async def ensure_indexes():
    # Ensure a unique email index for user collection
    await db.users.create_index("email", unique=True)


# -------------
# Authentication / User registration


@app.post("/register", response_model=UserRead)
async def register(user: UserRegister = Body(...)):
    hashed_password = get_password_hash(user.password)  # Ensure password field present in UserRegister
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    try:
        result = await db.users.insert_one(user_dict)
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already registered")

    created = await db.users.find_one({"_id": result.inserted_id})
    created["_id"] = str(created["_id"])
    created.pop("password", None)
    return UserRead(**created)


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Note: OAuth2PasswordRequestForm expects form data with 'username' (used for your email) and 'password'
    user_doc = await db.users.find_one({"email": form_data.username})
    if not user_doc or not verify_password(form_data.password, user_doc.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_data = {"sub": user_doc["email"]}
    access_token = create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserRead)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return UserRead(**current_user)


# User CRUD routes


@app.get("/test-db")
async def test_db():
    count = await db.users.count_documents({})
    return {"user_count": count}


@app.get("/users", response_model=List[UserRead])
async def get_users(
    limit: int = Query(10, ge=1, le=100),
    skip: int = Query(0, ge=0),
    name: str = Query(None),
    email: str = Query(None),
    current_user: dict = Depends(get_current_user),  # Protect endpoint
):
    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if email:
        query["email"] = {"$regex": email, "$options": "i"}

    users = []
    cursor = db.users.find(query).skip(skip).limit(limit)
    async for u in cursor:
        u_dict = dict(u)
        u_dict["_id"] = str(u_dict["_id"])
        u_dict.pop("password", None)
        users.append(UserRead(**u_dict))
    return users


@app.put("/users/{user_id}", response_model=UserRead)
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

    if user_update.email != existing_user.get("email"):
        duplicate_email = await db.users.find_one({"email": user_update.email})
        if duplicate_email:
            raise HTTPException(status_code=400, detail="Email already registered")

    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": user_update.dict()})

    updated_doc = await db.users.find_one({"_id": ObjectId(user_id)})
    updated_doc["_id"] = str(updated_doc["_id"])
    updated_doc.pop("password", None)
    return UserRead(**updated_doc)


@app.delete("/users/{user_id}")
async def delete_user(
    user_id: str = Path(...),
    current_user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    delete_result = await db.users.delete_one({"_id": ObjectId(user_id)})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return JSONResponse(content={"message": "User deleted successfully"})


@app.get("/")
async def root():
    return {"message": "Hello, Research AI Companion backend is up and running!"}


# Include the PDF upload router (secured with dependency injection in pdf.py)
app.include_router(pdf_router)
