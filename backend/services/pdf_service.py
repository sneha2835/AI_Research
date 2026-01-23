# backend/services/pdf_service.py

import re
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from backend.app.chroma_store import add_chunks_to_chroma
from backend.app.db import db


# --------------------------------------------------
# Section detection
# --------------------------------------------------

def detect_section(text: str) -> str:
    text_l = text.lower()
    if "abstract" in text_l[:200]:
        return "abstract"
    if "introduction" in text_l[:200]:
        return "introduction"
    if "references" in text_l[:200]:
        return "references"
    return "body"


# --------------------------------------------------
# Definition detection (🔥 critical for your issue)
# --------------------------------------------------

def contains_definition(text: str) -> bool:
    patterns = [
        r"define[d]? as",
        r"can be defined as",
        r"is defined as",
        r"understood as",
        r"no single agreed[- ]upon definition",
    ]
    text_l = text.lower()
    return any(re.search(p, text_l) for p in patterns)


# --------------------------------------------------
# PDF extraction + indexing
# --------------------------------------------------

async def extract_and_index_pdf(document: dict):
    reader = PdfReader(document["path"])
    full_text = ""

    for page in reader.pages:
        page_txt = page.extract_text()
        if page_txt:
            full_text += page_txt + "\n"

    # Base splitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""],
    )

    raw_chunks = splitter.split_text(full_text)

    chunks: list[Document] = []

    for raw in raw_chunks:
        section = detect_section(raw)

        # 🔥 Definition-aware sub-chunking
        if contains_definition(raw):
            sub_splitter = RecursiveCharacterTextSplitter(
                chunk_size=300,
                chunk_overlap=50,
                separators=["\n\n", "\n", " ", ""],
            )

            for sub in sub_splitter.split_text(raw):
                chunks.append(
                    Document(
                        page_content=sub,
                        metadata={
                            "metadata_id": str(document["_id"]),
                            "user_id": str(document["owner"])
                            if document.get("owner")
                            else None,
                            "section": "definition",
                        },
                    )
                )
        else:
            chunks.append(
                Document(
                    page_content=raw,
                    metadata={
                        "metadata_id": str(document["_id"]),
                        "user_id": str(document["owner"])
                        if document.get("owner")
                        else None,
                        "section": section,
                    },
                )
            )

    # 🔥 Add ALL chunks at once
    add_chunks_to_chroma(chunks, str(document["_id"]), document.get("owner"))

    # ✅ Mark document as indexed
    await db.documents.update_one(
        {"_id": document["_id"]},
        {"$set": {"indexed": True}},
    )
