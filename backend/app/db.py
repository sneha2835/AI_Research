# backend/app/db.py

from motor.motor_asyncio import AsyncIOMotorClient
from backend.app.config import settings

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DB_NAME]


async def check_mongo_connection():
    await client.admin.command("ping")


async def create_indexes():
    await db.users.create_index("email", unique=True)

    await db.documents.create_index([
        ("source", 1),
        ("external_id", 1),
    ])

    await db.chunks.create_index("document_id")

    await db.chat_history.create_index(
        [("document_id", 1), ("user_id", 1), ("timestamp", 1)]
    )

    await db.recent_views.create_index(
        [("user_id", 1), ("viewed_at", -1)]
    )
