# backend/services/pdf_service.py

from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

from backend.app.db import db
from backend.app.chroma_store import add_chunks_to_chroma


async def extract_and_index_pdf(file_doc: dict, user_id: str) -> int:
    """
    Extracts text from a PDF, chunks it, embeds it into Chroma,
    and records chunk metadata in MongoDB.

    Used by:
    - User PDF uploads
    - arXiv paper analysis

    Returns number of chunks created.
    """

    loader = PyPDFLoader(file_doc["path"])
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
        doc_id=str(file_doc["_id"]),
        user_id=user_id,
    )

    await db.chunks.insert_one({
        "metadata_id": str(file_doc["_id"]),
        "user_id": user_id,
        "created_at": datetime.utcnow(),
        "chunk_count": len(chunks),
    })

    return len(chunks)
