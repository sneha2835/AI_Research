from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
from dotenv import load_dotenv

from backend.routers import pdf_chunking, auth, users
from backend.app.db import check_mongo_connection

load_dotenv()

app = FastAPI(
    title="Research AI Companion",
    version="1.0.0",
    description="Backend for PDF-based AI companion with user authentication"
)

# Include routers in logical order
app.include_router(auth.auth_router)          # Authentication first
app.include_router(users.users_router)        # Users CRUD second
app.include_router(pdf_chunking.pdf_router)   # PDF endpoints last

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.get("/", summary="Root endpoint")
async def root():
    return {"message": "Research AI Companion backend is running!"}

@app.get("/health", summary="Health check")
async def health_check():
    try:
        await check_mongo_connection()
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "degraded", "db": "unreachable", "error": str(e)}
