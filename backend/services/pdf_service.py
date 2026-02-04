from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from pypdf import PdfReader
from backend.app.chroma_store import add_chunks_to_chroma
from backend.app.db import db


# ==================================================
# 🧠 Section detection (lightweight heuristic)
# ==================================================

def detect_section(text: str) -> str:
    text_l = text.lower()

    if "abstract" in text_l[:200]:
        return "abstract"
    if "introduction" in text_l[:200]:
        return "introduction"
    if "references" in text_l[:200]:
        return "references"

    return "body"


# ==================================================
# 📄 Extract + index PDF
# ==================================================

async def extract_and_index_pdf(document: dict):
    """
    Extracts text from a PDF, chunks it, embeds it,
    and marks the document as indexed.

    Works for BOTH:
    - arXiv papers
    - user uploads
    """

    # --------------------------------------------------
    # 🚫 Safety: do not re-index
    # --------------------------------------------------
    if document.get("indexed"):
        return

    reader = PdfReader(document["path"])
    full_text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            full_text += page_text + "\n"

    # ❌ Extraction failed → mark explicitly
    if not full_text.strip():
        await db.documents.update_one(
            {"_id": document["_id"]},
            {"$set": {"index_failed": True}},
        )
        return

    # --------------------------------------------------
    # ✂️ Chunking strategy
    # --------------------------------------------------
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""],
    )

    raw_chunks = splitter.split_text(full_text)

    chunks = []
    for raw in raw_chunks:
        section = detect_section(raw)

        chunks.append(
            Document(
                page_content=raw,
                metadata={
                    "metadata_id": str(document["_id"]),
                    "user_id": str(document["owner"]) if document.get("owner") else None,
                    "section": section,
                },
            )
        )

    # --------------------------------------------------
    # 🧠 Add to vector store
    # --------------------------------------------------
    add_chunks_to_chroma(chunks, str(document["_id"]))

    # --------------------------------------------------
    # ✅ Mark document as indexed
    # --------------------------------------------------
    await db.documents.update_one(
        {"_id": document["_id"]},
        {"$set": {"indexed": True}},
    )
