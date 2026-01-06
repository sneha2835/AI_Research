# backend/app/llm_inference.py

import threading
from transformers import pipeline

# ---------------- GLOBALS ----------------
_lock = threading.Lock()
_text2text = None

MODEL_NAME = "google/flan-t5-base"


def _load_model():
    """Lazy-load model once (CPU, deterministic)."""
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
            device=-1,
            max_new_tokens=150,
            do_sample=False,
            repetition_penalty=1.3,     # ⭐ IMPORTANT
            num_beams=4                 # ⭐ IMPORTANT
)


# ---------------- QA ----------------
def answer_from_context(prompt: str) -> str:
    _load_model()

    if not prompt.strip():
        return "No prompt provided."

    result = _text2text(
        prompt,
        max_new_tokens=200,
        truncation=True,
    )

    if not result or "generated_text" not in result[0]:
        return "The model did not return an answer."

    answer = result[0]["generated_text"].strip()

    if not answer:
        return "The model could not generate an answer."

    return answer


# ---------------- SUMMARY ----------------
def summarize_text(text: str) -> str:
    _load_model()

    if not text.strip():
        return "No text provided."

    prompt = f"""
Summarize the following text clearly and concisely:

{text}

Summary:
""".strip()

    result = _text2text(
        prompt,
        max_new_tokens=200,
        truncation=True,
    )

    if not result:
        return "Summary could not be generated."

    return result[0]["generated_text"].strip()
