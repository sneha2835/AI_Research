# backend/app/db.py

from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

# --------------------------------------------------
# MongoDB client (single global connection)
# --------------------------------------------------

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DB_NAME]


async def check_mongo_connection():
    """
    Lightweight health check.
    Called on app startup and /health endpoint.
    """
    await client.admin.command("ping")


async def create_indexes():
    """
    Centralized index creation.
    Safe to run multiple times (idempotent).
    """

    # ==================================================
    # 👤 Users
    # ==================================================

    # Enforce unique emails
    await db.users.create_index(
        "email",
        unique=True,
        name="users_email_unique"
    )

    # ==================================================
    # 📄 Documents (uploads + arXiv)
    # ==================================================

    # Prevent duplicate arXiv documents (shared globally)
    await db.documents.create_index(
        [("source", 1), ("external_id", 1)],
        unique=True,
        name="documents_arxiv_unique",
        partialFilterExpression={"source": "arxiv"},
    )

    # Fast ownership + source checks
    await db.documents.create_index(
        [("owner", 1), ("source", 1)],
        name="documents_owner_source"
    )

    # Quickly find documents pending indexing
    await db.documents.create_index(
        "indexed",
        name="documents_indexed_flag"
    )
    await db.documents.create_index(
        "ready_for_chat",
        name="documents_ready_flag"
    )


    # ==================================================
    # 📚 Research papers (arXiv metadata)
    # ==================================================

    # Dashboard: recent papers
    await db.research_papers.create_index(
        [("published", -1)],
        name="research_papers_published_desc"
    )

    # ==================================================
    # 💬 Chat history
    # ==================================================

    # Load chat history efficiently per document + user
    await db.chat_history.create_index(
        [("document_id", 1), ("user_id", 1), ("timestamp", 1)],
        name="chat_history_lookup"
    )

    # Auto-clean old chats after 180 days
    await db.chat_history.create_index(
        "timestamp",
        expireAfterSeconds=60 * 60 * 24 * 180,
        name="chat_history_ttl"
    )

    # ==================================================
    # 🕘 Recently viewed (uploads + arXiv)
    # ==================================================

    # Fetch recent views quickly
    await db.recent_views.create_index(
        [("user_id", 1), ("viewed_at", -1)],
        name="recent_views_user_time"
    )

    # One arXiv view per user per paper
    await db.recent_views.create_index(
        [("user_id", 1), ("paper_id", 1)],
        unique=True,
        name="recent_views_arxiv_unique",
        partialFilterExpression={"type": "arxiv"},
    )

    # One upload view per user per document
    await db.recent_views.create_index(
        [("user_id", 1), ("document_id", 1)],
        unique=True,
        name="recent_views_upload_unique",
        partialFilterExpression={"type": "upload"},
    )

    # Auto-clean recent views after 90 days
    await db.recent_views.create_index(
        "viewed_at",
        expireAfterSeconds=60 * 60 * 24 * 90,
        name="recent_views_ttl"
    )
