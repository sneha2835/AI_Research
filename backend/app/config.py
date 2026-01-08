# backend/app/config.py

from pydantic_settings import BaseSettings
from pydantic import field_validator


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
    HF_TOKEN: str | None = None

    # --------------------
    # ENV config
    # --------------------
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    # --------------------
    # FORCE BOOLEAN PARSING
    # --------------------
    @field_validator("ENABLE_CHROMA", mode="before")
    @classmethod
    def parse_enable_chroma(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in {"1", "true", "yes", "on"}
        return bool(v)


# ✅ Singleton settings instance
settings = Settings()
