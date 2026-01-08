# backend/app/llm_inference.py

import threading
from transformers import pipeline
from backend.app.config import settings

_lock = threading.Lock()
_text2text = None


def _load_model():
    global _text2text

    if _text2text is not None:
        return

    with _lock:
        if _text2text is not None:
            return

        _text2text = pipeline(
            "text2text-generation",
            model=settings.HF_MODEL,
            tokenizer=settings.HF_MODEL,
            device=-1,
            max_new_tokens=200,
            do_sample=False,
            repetition_penalty=1.3,
            num_beams=4,
        )


def answer_from_context(prompt: str) -> str:
    _load_model()

    if not prompt.strip():
        return "No prompt provided."

    result = _text2text(prompt, truncation=True)

    if not result:
        return "No answer generated."

    return result[0]["generated_text"].strip()


def summarize_text(text: str) -> str:
    _load_model()

    if not text.strip():
        return "No text provided."

    prompt = f"Summarize the following text:\n\n{text}\n\nSummary:"
    result = _text2text(prompt, truncation=True)

    return result[0]["generated_text"].strip() if result else "Summary failed."
