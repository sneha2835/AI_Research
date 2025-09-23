from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HF_MODEL = os.getenv("HF_MODEL")
HF_TOKEN = os.getenv("HF_TOKEN")

device = "cpu"

print(f"Loading tokenizer for {HF_MODEL}...")
tokenizer = AutoTokenizer.from_pretrained(HF_MODEL, token=HF_TOKEN)

# BitsAndBytesConfig for 4-bit quantization on CPU
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float32,  # CPU friendly
    llm_int8_enable_fp32_cpu_offload=True  # keep layers in fp32 on CPU if needed
)

print(f"Loading model {HF_MODEL} in 4-bit on CPU...")
model = AutoModelForCausalLM.from_pretrained(
    HF_MODEL,
    quantization_config=bnb_config,
    device_map={"": "cpu"},  # force all layers to CPU
    token=HF_TOKEN
)

prompt = "Write a short poem about the ocean."
inputs = tokenizer(prompt, return_tensors="pt").to(device)

print("Generating text...")
with torch.no_grad():
    output_ids = model.generate(
        **inputs,
        max_new_tokens=100,
        do_sample=True,
        temperature=0.7
    )

output_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
print("\n--- Generated Text ---\n")
print(output_text)
