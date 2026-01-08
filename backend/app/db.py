# backend/app/db.py

from motor.motor_asyncio import AsyncIOMotorClient
from backend.app.config import settings

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DB_NAME]


async def check_mongo_connection():
    try:
        await client.admin.command("ping")
        return True
    except Exception as e:
        raise RuntimeError(f"MongoDB connection failed: {e}")


async def create_indexes():
    """
    Call once at startup.
    """
    await db.users.create_index("email", unique=True)
    await db.pdf_files.create_index("user_id")
    await db.chunks.create_index("metadata_id")
    await db.chat_history.create_index(
        [("metadata_id", 1), ("user_id", 1), ("timestamp", 1)]
    )
    # Research papers (arXiv)
    await db.research_papers.create_index(
        "pdf_url",
        unique=True
    )

    await db.research_papers.create_index(
        [("published", -1)]
    )

    # Recently viewed papers
    await db.recent_views.create_index(
        [("user_id", 1), ("viewed_at", -1)]
    )

