# backend/app/db.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "research_db")

# MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


async def check_mongo_connection():
    """Check MongoDB connection by pinging the server."""
    try:
        await client.admin.command("ping")
        return True
    except Exception as e:
        raise RuntimeError(f"MongoDB connection failed: {str(e)}")
