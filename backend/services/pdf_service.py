# backend/services/pdf_service.py

from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from backend.app.db import db
from backend.app.chroma_store import add_chunks_to_chroma


async def extract_and_index_pdf(document: dict) -> int:
    """
    Extracts PDF → chunks → embeddings.
    Runs ONCE per document.
    """

    existing = await db.chunks.find_one({
        "document_id": str(document["_id"])
    })
    if existing:
        return existing["chunk_count"]

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
        chunks,
        doc_id=str(document["_id"]),
    )

    await db.chunks.insert_one({
        "document_id": str(document["_id"]),
        "created_at": datetime.utcnow(),
        "chunk_count": len(chunks),
    })

    return len(chunks)
