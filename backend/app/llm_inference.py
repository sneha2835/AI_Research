# backend/app/llm_inference.py

import threading
from transformers import pipeline
from backend.app.prompts import QA_PROMPT, SUMMARY_PROMPT

# ---------------- GLOBALS ----------------
_lock = threading.Lock()
_text2text = None

MODEL_NAME = "google/flan-t5-base"   # ✅ Google model


def _load_model():
    """
    Lazy-load model once.
    CPU-only, deterministic, no hallucinations.
    """
    global _text2text
    if _text2text is not None:
        return

    with _lock:
        if _text2text is not None:
            return

        _text2text = pipeline(
            "text2text-generation",
            model=MODEL_NAME,
            tokenizer=MODEL_NAME,
            device=-1,               # CPU
            max_new_tokens=200,
            do_sample=False          # IMPORTANT: disables hallucination
        )


# ---------------- QA ----------------
def answer_from_context(context: str, question: str) -> str:
    _load_model()

    if not context.strip():
        return "I could not find this information in the document."

    # HARD truncate context (FLAN max ~512 tokens)
    words = context.split()
    if len(words) > 350:
        context = " ".join(words[:350])

    prompt = QA_PROMPT.format(
        context=context.strip(),
        question=question.strip()
    )

    result = _text2text(prompt)
    return result[0]["generated_text"].strip()


# ---------------- SUMMARY ----------------
def summarize_text(text: str) -> str:
    _load_model()

    # HARD truncate
    words = text.split()
    if len(words) > 300:
        text = " ".join(words[:300])

    prompt = SUMMARY_PROMPT.format(text=text.strip())

    result = _text2text(prompt)
    return result[0]["generated_text"].strip()
