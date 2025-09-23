import os
import threading

HUGGINGFACE_MODEL = os.getenv("HF_MODEL", "microsoft/phi-3-mini-128k-instruct")

if os.getenv("HF_HOME"):
    os.environ['HF_HOME'] = os.getenv('HF_HOME')
if os.getenv('TRANSFORMERS_CACHE'):
    os.environ['TRANSFORMERS_CACHE'] = os.getenv('TRANSFORMERS_CACHE')
if os.getenv('HUGGINGFACE_HUB_CACHE'):
    os.environ['HUGGINGFACE_HUB_CACHE'] = os.getenv('HUGGINGFACE_HUB_CACHE')

_llm_lock = threading.Lock()
_llm_pipeline = None


def _ensure_llm_loaded():
    global _llm_pipeline
    if _llm_pipeline is not None:
        return

    with _llm_lock:
        if _llm_pipeline is not None:
            return
        from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

        tokenizer = AutoTokenizer.from_pretrained(HUGGINGFACE_MODEL, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(HUGGINGFACE_MODEL, trust_remote_code=True)

        _llm_pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=int(os.getenv("LLM_MAX_NEW_TOKENS", 300)),
            temperature=float(os.getenv("LLM_TEMPERATURE", 0.3)),
        )


def generate_answer(prompt: str) -> str:
    _ensure_llm_loaded()
    outputs = _llm_pipeline(prompt)
    text = outputs[0]["generated_text"]
    if text.startswith(prompt):
        return text[len(prompt):].strip()
    return text.strip()


def generate_summary(prompt: str) -> str:
    return generate_answer(prompt)


def generate_followup_questions(prompt: str) -> str:
    return generate_answer(prompt)
