from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "distilgpt2"  # Your current model

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

print("Model loaded successfully")
