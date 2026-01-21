# backend/app/db.py

from motor.motor_asyncio import AsyncIOMotorClient
from backend.app.config import settings

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DB_NAME]


async def check_mongo_connection():
    await client.admin.command("ping")


async def create_indexes():
    # -------------------------
    # Users
    # -------------------------
    await db.users.create_index("email", unique=True)

    # -------------------------
    # Documents
    # -------------------------
    await db.documents.create_index([
        ("source", 1),
        ("external_id", 1),
    ])

    # 🔥 NEW: Faster ownership checks
    await db.documents.create_index([
        ("owner", 1),
        ("source", 1),
    ])
    await db.documents.create_index("indexed")
    # -------------------------
    # Research papers (dashboard)
    # -------------------------
    await db.research_papers.create_index([
        ("published", -1)
    ])

    # -------------------------
    # Chat history
    # -------------------------
    await db.chat_history.create_index(
        [("document_id", 1), ("user_id", 1), ("timestamp", 1)]
    )

    # 🔥 NEW: Auto-cleanup chat after 180 days
    await db.chat_history.create_index(
        "timestamp",
        expireAfterSeconds=60 * 60 * 24 * 180  # 180 days
    )

    # -------------------------
    # Recent views
    # -------------------------
    await db.recent_views.create_index(
        [("user_id", 1), ("viewed_at", -1)]
    )

    # 🔥 NEW: Enforce ONE view per user per document
    # arXiv views
    await db.recent_views.create_index(
        [("user_id", 1), ("paper_id", 1)],
        unique=True,
        partialFilterExpression={"type": "arxiv"},
    )

    # uploaded PDFs
    await db.recent_views.create_index(
        [("user_id", 1), ("document_id", 1)],
        unique=True,
        partialFilterExpression={"type": "upload"},
    )

    # 🔥 Auto-clean recent views after 90 days
    await db.recent_views.create_index(
        "viewed_at",
        expireAfterSeconds=60 * 60 * 24 * 90
    )


