# backend/app/main.py
# CORS fix applied

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from backend.routers import papers
from backend.routers import auth, users, pdf_chunking
from backend.app.db import check_mongo_connection, create_indexes
from backend.routers.chat import chat_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Research AI Companion",
    version="1.1.0",
)

# CORS middleware MUST be added before routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.auth_router)
app.include_router(users.users_router)
app.include_router(pdf_chunking.pdf_router)
app.include_router(papers.papers_router)
app.include_router(chat_router)


@app.on_event("startup")
async def startup():
    # Temporarily disabled to fix CORS issues
    # TODO: Re-enable after testing
    logging.info("✅ Startup complete (MongoDB checks disabled)")
    pass


@app.get("/")
async def root():
    return {"status": "running"}


@app.get("/health")
async def health():
    try:
        await check_mongo_connection()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}
