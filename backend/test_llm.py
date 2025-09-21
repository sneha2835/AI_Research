# test_llm_phi3.py
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# Model selection
model_name = "microsoft/phi-3-mini-128k-instruct"

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Load model (CPU)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",  # will use CPU
    torch_dtype="auto"  # let HF decide best dtype
)

# Create a text-generation pipeline
llm_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer)

# Example input (you can replace this with PDF-extracted text)
input_text = """
Summarize the following research text: 
'The study explores the impact of climate change on crop yields over the past 50 years, 
highlighting the importance of adaptive farming techniques.'
"""

# Generate summary
output = llm_pipeline(input_text, max_length=150, do_sample=True, temperature=0.7)

print("=== Generated Output ===")
print(output[0]['generated_text'])
