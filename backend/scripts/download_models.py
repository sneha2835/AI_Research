"""
Download and verify all ML models required by the backend.

- Uses HuggingFace cache (no re-downloads if already present)
- Explicitly reports when cached models are reused
- Verifies models can be loaded
- Safe for low-storage machines
- Windows-safe (no symlink privileges required)

Usage:
    python backend/scripts/download_models.py
"""

import sys
from pathlib import Path
from huggingface_hub import snapshot_download
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    PegasusTokenizer,
    PegasusForConditionalGeneration,
)
from sentence_transformers import SentenceTransformer


# ============================================================
# Model configuration (single source of truth)
# ============================================================

EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
QA_MODEL = "google/flan-t5-large"
SUMMARY_MODEL = "google/pegasus-arxiv"


# ============================================================
# Cache helpers
# ============================================================

def ensure_model_cached(repo_id: str) -> Path:
    """
    Ensure a model is present in the local HuggingFace cache.
    If already cached, it will NOT be re-downloaded.
    """
    print(f"\n🔍 Checking cache for: {repo_id}")
    path = snapshot_download(
        repo_id=repo_id,
        local_files_only=False,        # allow download if missing
        resume_download=True,          # resume partial downloads
        local_dir_use_symlinks=False   # Windows-safe (NO symlinks)
    )
    print(f"✅ Cached at: {path}")
    return Path(path)


# ============================================================
# Load / verify helpers
# ============================================================

def load_embedding_model():
    ensure_model_cached(EMBEDDING_MODEL)
    print(f"🔹 Loading embedding model: {EMBEDDING_MODEL}")
    SentenceTransformer(EMBEDDING_MODEL)
    print("✅ Embedding model ready")


def load_seq2seq_model(model_name: str):
    ensure_model_cached(model_name)
    print(f"🔹 Loading model: {model_name}")
    AutoTokenizer.from_pretrained(model_name)
    AutoModelForSeq2SeqLM.from_pretrained(model_name)
    print(f"✅ Model '{model_name}' ready")


def load_pegasus_model():
    ensure_model_cached(SUMMARY_MODEL)
    print(f"🔹 Loading summarization model: {SUMMARY_MODEL}")
    try:
        PegasusTokenizer.from_pretrained(SUMMARY_MODEL)
        PegasusForConditionalGeneration.from_pretrained(SUMMARY_MODEL)
    except ModuleNotFoundError as e:
        if "sentencepiece" in str(e).lower():
            print("\n❌ Missing dependency: sentencepiece\n")
            print("Install it with:\n")
            print("    pip install sentencepiece\n")
            raise
        raise
    print(f"✅ Model '{SUMMARY_MODEL}' ready")


# ============================================================
# Main execution
# ============================================================

def main():
    print("\n🚀 Verifying ML models (cache-aware)...\n")

    failures = []

    try:
        load_embedding_model()
    except Exception as e:
        failures.append(("embedding model", e))

    try:
        load_seq2seq_model(QA_MODEL)
    except Exception as e:
        failures.append(("QA model", e))

    try:
        load_pegasus_model()
    except Exception as e:
        failures.append(("summarization model", e))

    print("\n" + "-" * 45)

    if failures:
        print("⚠️ Some models failed to load:\n")
        for name, err in failures:
            print(f"- {name}: {err}")
        print("\n❌ Fix the above issues before running the backend.")
        sys.exit(1)

    print("🎉 ALL MODELS READY (CACHED OR DOWNLOADED)")
    print("No duplicate storage used.")
    print("You can now safely start the backend.\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
