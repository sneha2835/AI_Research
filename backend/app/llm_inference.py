import os
os.environ['HF_HOME'] = r'D:\huggingface_cache'
os.environ['TRANSFORMERS_CACHE'] = r'D:\huggingface_cache\models'
os.environ['HUGGINGFACE_HUB_CACHE'] = r'D:\huggingface_cache\hub'

print("HF_HOME =", os.getenv("HF_HOME"))
print("TRANSFORMERS_CACHE =", os.getenv("TRANSFORMERS_CACHE"))
print("HUGGINGFACE_HUB_CACHE =", os.getenv("HUGGINGFACE_HUB_CACHE"))

from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import threading

# Load model and tokenizer once globally
# You can replace "microsoft/phi-3-mini-4k-instruct" with your chosen compatible model
tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3.5-mini-instruct",trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained("microsoft/Phi-3.5-mini-instruct",trust_remote_code=True)

# Thread-safe pipeline for text generation
llm = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=300,
    temperature=0.3
)


def generate_answer(prompt: str) -> str:
    """Generate answer from prompt using LLM"""
    outputs = llm(prompt)
    text = outputs[0]["generated_text"]
    # Remove prompt from generated text
    return text[len(prompt):].strip()


def generate_summary(prompt: str) -> str:
    """Generate summary (paragraph or bullet points)"""
    return generate_answer(prompt)


def generate_followup_questions(prompt: str) -> str:
    """Generate follow up questions list"""
    return generate_answer(prompt)
