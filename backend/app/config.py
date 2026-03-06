# backend/app/config.py

from pydantic_settings import BaseSettings
from pydantic import field_validator
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


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
    # Vector Store / Chroma
    # --------------------
    CHROMA_PERSIST_DIR: str = "./chroma_persist"
    SENTENCE_EMBED_MODEL: str = "BAAI/bge-base-en-v1.5"
    ENABLE_CHROMA: bool = True

    # --------------------
    # Ollama (Local LLM)
    # --------------------
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3:mini"
    LLM_TEMP: float = 0.2
    LLM_MAX_TOKENS: int = 1000

    # --------------------
    # MongoDB (optional alias)
    # --------------------
    MONGO_URI: str | None = None

    # --------------------
    # Pydantic v2 env config
    # --------------------
    model_config = {
        "env_file": BASE_DIR / ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow",
    }

    # --------------------
    # Force boolean parsing
    # --------------------
    @field_validator("ENABLE_CHROMA", mode="before")
    @classmethod
    def parse_enable_chroma(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in {"1", "true", "yes", "on"}
        return bool(v)


# Singleton settings instance
settings = Settings()