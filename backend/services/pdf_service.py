# backend/services/pdf_service.py

import os
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from backend.app.db import db
from backend.app.chroma_store import add_chunks_to_chroma

async def extract_and_index_pdf(document: dict) -> int:
    """
    Extracts PDF → chunks → embeddings.
    Runs ONLY ONCE per document.
    """

    # already indexed
    existing = await db.chunks.find_one({
        "document_id": str(document["_id"])
    })
    if existing:
        return existing["chunk_count"]

    # safety guard
    if not document.get("path") or not os.path.exists(document["path"]):
        return 0

    loader = PyPDFLoader(document["path"])
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
    )
    chunks = splitter.split_documents(docs)

    if not chunks:
        return 0

    add_chunks_to_chroma(
        chunks=chunks,
        doc_id=str(document["_id"]),
        user_id=document.get("owner"),
    )

    await db.chunks.insert_one({
        "document_id": str(document["_id"]),
        "created_at": datetime.utcnow(),
        "chunk_count": len(chunks),
    })

    return len(chunks)
