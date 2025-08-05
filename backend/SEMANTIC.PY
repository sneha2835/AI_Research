import sys
import os
import chromadb


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.chroma_store import semantic_search

chunks = semantic_search("What is the primary objective of the War Spying Robot with Wireless Night Vision Camera project?", 5)
print(f"Found {len(chunks)} chunks")
for c in chunks:
    print(c.page_content[:200])  # preview first 200 chars