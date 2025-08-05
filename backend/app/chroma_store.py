from dotenv import load_dotenv
load_dotenv()

import os
print("GOOGLE_APPLICATION_CREDENTIALS:", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

import chromadb
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

client = chromadb.Client()

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

vector_store = Chroma(
    collection_name="pdf_chunks",
    client=client,
    embedding_function=embeddings,
    persist_directory="./chroma_persist"
)

def add_chunks_to_chroma(text_chunks, doc_id: str):
    texts = [chunk.page_content for chunk in text_chunks]  # Extract raw text
    metadatas = [{"page_number": chunk.metadata.get("page", -1)} for chunk in text_chunks]
    ids = [f"{doc_id}_{i}" for i in range(len(text_chunks))]

    vector_store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    vector_store.persist()

def semantic_search(query: str, n_results=5):
    return vector_store.similarity_search(query, k=n_results)
