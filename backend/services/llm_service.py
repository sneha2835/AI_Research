# backend/services/llm_service.py

from backend.app.config import settings
from transformers import pipeline

# Load once (important)
_llm = pipeline(
    "text2text-generation",
    model=settings.HF_MODEL,
    token=settings.HF_TOKEN,
    max_new_tokens=256,
)

def answer_from_context(prompt: str) -> str:
    try:
        if not prompt.strip():
            return ""

        result = _llm(prompt)
        if not result or not isinstance(result, list):
            return ""

        text = result[0].get("generated_text", "").strip()
        return text
    except Exception as e:
        print("LLM ERROR:", e)
        return ""
