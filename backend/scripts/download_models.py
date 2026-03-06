"""
Download and verify required ML models for the backend.

Current setup:
- Embeddings: BAAI/bge-base-en-v1.5 (HuggingFace)
- Generation: llama3:8b via Ollama (handled separately)

Usage:
    python backend/scripts/download_models.py
"""

import sys
from pathlib import Path
from huggingface_hub import snapshot_download
from sentence_transformers import SentenceTransformer


# ============================================================
# Model configuration
# ============================================================

EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"


# ============================================================
# Cache helper
# ============================================================

def ensure_model_cached(repo_id: str) -> Path:
    print(f"\n🔍 Checking cache for: {repo_id}")
    path = snapshot_download(
        repo_id=repo_id,
        local_files_only=False,
        resume_download=True,
        local_dir_use_symlinks=False
    )
    print(f"✅ Cached at: {path}")
    return Path(path)


# ============================================================
# Load / verify embedding model
# ============================================================

def load_embedding_model():
    ensure_model_cached(EMBEDDING_MODEL)
    print(f"🔹 Loading embedding model: {EMBEDDING_MODEL}")
    SentenceTransformer(EMBEDDING_MODEL)
    print("✅ Embedding model ready")


# ============================================================
# Main
# ============================================================

def main():
    print("\n🚀 Verifying embedding model (cache-aware)...\n")

    try:
        load_embedding_model()
    except Exception as e:
        print(f"\n❌ Failed to load embedding model: {e}")
        sys.exit(1)

    print("\n" + "-" * 45)
    print("🎉 EMBEDDING MODEL READY")
    print("\n⚠️  IMPORTANT:")
    print("Make sure Ollama is installed and run:")
    print("    ollama pull llama3:8b")
    print("before starting the backend.\n")

    sys.exit(0)


if __name__ == "__main__":
    main()