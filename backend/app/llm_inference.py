# backend/app/llm_inference.py

import threading
from transformers import pipeline
from backend.app.config import settings

_lock = threading.Lock()

_qa_pipeline = None
_summary_pipeline = None


def _load_qa():
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
            max_new_tokens=180,
            do_sample=False,
            num_beams=1,
            repetition_penalty=2.2,
            no_repeat_ngram_size=4,
        )


def _load_summary():
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
            max_length=220,
            min_length=90,
            do_sample=False,
            repetition_penalty=2.5,
            no_repeat_ngram_size=4,
        )


# -------------------------
# Public APIs
# -------------------------

def answer_from_context(prompt: str) -> str:
    _load_qa()

    if not prompt.strip():
        return ""

    result = _qa_pipeline(prompt, truncation=True)
    if not result:
        return ""

    return result[0]["generated_text"].strip()


def summarize_text(text: str) -> str:
    _load_summary()

    if not text.strip():
        return ""

    result = _summary_pipeline(text, truncation=True)
    if not result:
        return ""

    return result[0]["summary_text"].strip()
