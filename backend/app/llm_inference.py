import threading
from transformers import pipeline
from app.config import settings

# ==================================================
# 🔒 Thread-safe lazy loading
# ==================================================

_lock = threading.Lock()

_qa_pipeline = None
_summary_pipeline = None

# ==================================================
# 🧠 Loaders
# ==================================================

def _load_qa_pipeline():
    global _qa_pipeline
    if _qa_pipeline is not None:
        return

    with _lock:
        if _qa_pipeline is not None:
            return

        _qa_pipeline = pipeline(
            "text2text-generation",
            model=settings.HF_QA_MODEL,
            token=settings.HF_TOKEN,
            max_new_tokens=256,
            do_sample=False,
            repetition_penalty=1.8,
            no_repeat_ngram_size=3,
        )


def _load_summary_pipeline():
    global _summary_pipeline
    if _summary_pipeline is not None:
        return

    with _lock:
        if _summary_pipeline is not None:
            return

        _summary_pipeline = pipeline(
            "summarization",
            model=settings.HF_SUMMARY_MODEL,
            token=settings.HF_TOKEN,
            max_length=240,
            min_length=80,
            do_sample=False,
            repetition_penalty=2.0,
            no_repeat_ngram_size=3,
        )

# ==================================================
# ❓ Question answering
# ==================================================

def answer_from_context(prompt: str) -> str:
    """
    Expects a fully-formed prompt.
    Backend does NOT add logic here.
    """

    if not prompt or not prompt.strip():
        return ""

    _load_qa_pipeline()

    try:
        result = _qa_pipeline(prompt, truncation=True)
    except Exception:
        return ""

    if not result:
        return ""

    return result[0].get("generated_text", "").strip()

# ==================================================
# 📝 Summarization
# ==================================================

def summarize_text(prompt: str) -> str:
    """
    Expects a structured summarization prompt.
    """

    if not prompt or not prompt.strip():
        return ""

    _load_summary_pipeline()

    try:
        result = _summary_pipeline(prompt, truncation=True)
    except Exception:
        return ""

    if not result:
        return ""

    return result[0].get("summary_text", "").strip()
