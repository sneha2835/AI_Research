# backend/services/pdf_service.py

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from backend.app.chroma_store import add_chunks_to_chroma
from pypdf import PdfReader

def detect_section(text: str) -> str:
    text_l = text.lower()
    if "abstract" in text_l[:200]:
        return "abstract"
    if "introduction" in text_l[:200]:
        return "introduction"
    if "references" in text_l[:200]:
        return "references"
    return "body"

async def extract_and_index_pdf(document: dict):
    reader = PdfReader(document["path"])
    text = ""

    for page in reader.pages:
        page_txt = page.extract_text()
        if page_txt:
            text += page_txt + "\n"

    # cleaner split
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""]
    )

    raw_chunks = splitter.split_text(text)

    from langchain.schema import Document
    chunks = []
    for raw in raw_chunks:
        section = detect_section(raw)
        chunks.append(Document(
            page_content=raw,
            metadata={
                "metadata_id": str(document["_id"]),
                "user_id": str(document["owner"]),
                "section": section,
            },
        ))

    add_chunks_to_chroma(chunks, str(document["_id"]), document["owner"])