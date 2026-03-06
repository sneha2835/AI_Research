# app/llm_inference.py

import requests
from app.config import settings


def _call_ollama(prompt: str) -> str:
    try:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": settings.LLM_TEMP,
                    "num_predict": settings.LLM_MAX_TOKENS,
                },
            },
            timeout=300,
        )

        if response.status_code != 200:
            print("⚠️ Ollama HTTP error:", response.text)
            return ""

        data = response.json()
        print("RAW OLLAMA RESPONSE:", data)  # <-- Debug here

        return data.get("response", "").strip()

    except Exception as e:
        print("⚠️ Ollama call failed:", e)
        return ""

# --------------------------------------------------
# Generic Generation
# --------------------------------------------------

def generate_text(prompt: str) -> str:
    if not prompt or not prompt.strip():
        return ""
    return _call_ollama(prompt)


# --------------------------------------------------
# Follow-up Generator
# --------------------------------------------------

def generate_followups(question: str, answer: str) -> list[str]:
    followup_prompt = f"""
You are a research assistant.

Based on this conversation:

Question:
{question}

Answer:
{answer}

Generate exactly 3 short and relevant follow-up questions.
Return them as a numbered list.
Do not include explanations.
""".strip()

    raw = _call_ollama(followup_prompt)

    if not raw:
        return []

    lines = [
        line.strip().lstrip("1234567890. ").strip()
        for line in raw.split("\n")
        if line.strip()
    ]

    return lines[:3]