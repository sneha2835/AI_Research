# backend/app/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --------------------
    # Security
    # --------------------
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --------------------
    # Database
    # --------------------
    MONGO_URL: str = "mongodb://localhost:27017"
    DB_NAME: str = "research_db"

    # --------------------
    # Vector store / Chroma
    # --------------------
    CHROMA_PERSIST_DIR: str = "./chroma_persist"
    SENTENCE_EMBED_MODEL: str = "BAAI/bge-base-en-v1.5"
    ENABLE_CHROMA: bool = True

    # --------------------
    # LLM / HuggingFace
    # --------------------
    HF_MODEL: str = "google/flan-t5-base"
    HF_TOKEN: str | None = None  # optional

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
