# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging

from routers import papers
from routers import auth, users, pdf_chunking
from routers.chat import chat_router
from routers.dashboard import dashboard_router
from routers.google_auth import router as google_auth_router


from app.db import check_mongo_connection, create_indexes


logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Research AI Companion",
    version="1.1.0",
)

# ✅ Serve uploaded PDFs as static files
# This allows access via:
# http://localhost:8001/pdf_uploads/<document_id>.pdf
app.mount(
    "/pdf_uploads",
    StaticFiles(directory="pdf_uploads"),
    name="pdf_uploads",
)

# ✅ CORS middleware (keep before routers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development. Restrict in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include all routers
app.include_router(auth.auth_router)
app.include_router(google_auth_router)
app.include_router(users.users_router)
app.include_router(dashboard_router)
app.include_router(pdf_chunking.pdf_router)
app.include_router(papers.papers_router)
app.include_router(chat_router)


@app.on_event("startup")
async def startup():
    logging.info("🚀 Backend started successfully")
    # Optional: enable these later if needed
    await check_mongo_connection()
    await create_indexes()
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
