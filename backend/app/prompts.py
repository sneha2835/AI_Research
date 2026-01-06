# backend/app/prompts.py

QA_PROMPT = """
You are an AI research assistant.

Answer the question ONLY using the context below.
If the answer is not explicitly present, reply exactly:
"I could not find this information in the document."

Context:
{context}

Question:
{question}

Answer:
"""

SUMMARY_PROMPT = """
Summarize the following text into a concise academic paragraph.
Do not add information not present in the text.

Text:
{text}

Summary:
"""
