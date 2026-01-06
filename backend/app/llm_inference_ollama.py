import os
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

def generate_answer(prompt: str) -> str:
    """Generate answer using Ollama API"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": "llama2",  # You can use llama2, mistral, or other models
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get("response", "No response generated")
        else:
            return "Unable to generate answer at this time."
    except Exception as e:
        print(f"Ollama error: {e}")
        return "Service temporarily unavailable."


def generate_summary(prompt: str) -> str:
    return generate_answer(prompt)


def generate_followup_questions(prompt: str) -> str:
    return generate_answer(prompt)
