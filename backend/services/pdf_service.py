import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from pypdf import PdfReader

from app.chroma_store import add_chunks_to_chroma, GLOBAL_OWNER
from app.db import db


# ==================================================
# 🧠 Robust Section Detection
# ==================================================

SECTION_REGEX = re.compile(
    r"(?i)^\s*(?:[ivx]+\s*\.?\s*)?"
    r"(abstract|introduction|literature review|related work|"
    r"methodology|methods?|system design|implementation|"
    r"results?|discussion|conclusion|future work|references)\b"
)


def normalize_section(name: str) -> str:
    name = name.lower().strip()

    mapping = {
        "methods": "methodology",
        "result": "results",
        "system design": "methodology",
        "implementation": "methodology",
        "future work": "conclusion",
    }

    return mapping.get(name, name)


# ==================================================
# 📄 Extract + Index PDF (Structured + Robust)
# ==================================================

async def extract_and_index_pdf(document: dict):
    """
    Extracts text from PDF, detects sections,
    chunks intelligently, and stores in Chroma.
    """

    # 🚫 Prevent re-indexing
    if document.get("indexed"):
        return

    reader = PdfReader(document["path"])
    full_text = ""

    # --------------------------------------------------
    # 📄 Extract Text
    # --------------------------------------------------

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            full_text += page_text + "\n"

    if not full_text.strip():
        await db.documents.update_one(
            {"_id": document["_id"]},
            {"$set": {"index_failed": True}},
        )
        return

    # --------------------------------------------------
    # 🧠 Structured Section Parsing
    # --------------------------------------------------

    lines = full_text.split("\n")
    sections = []

    current_section = "unknown"
    buffer = []

    for line in lines:
        stripped = line.strip()
        match = SECTION_REGEX.search(stripped)

        if match:
            # Save previous section
            if buffer:
                sections.append((current_section, "\n".join(buffer)))
                buffer = []

            detected = normalize_section(match.group(1))
            current_section = detected

        buffer.append(line)

    if buffer:
        sections.append((current_section, "\n".join(buffer)))

    # --------------------------------------------------
    # ⚠️ Fallback if no sections detected
    # --------------------------------------------------

    detected_sections = {sec for sec, _ in sections}

    if detected_sections == {"unknown"}:
        sections = [("body", full_text)]

    # --------------------------------------------------
    # 🚫 Remove references (noise reduction)
    # --------------------------------------------------

    sections = [
        (sec, text)
        for sec, text in sections
        if sec.lower() != "references"
    ]

    # --------------------------------------------------
    # ✂️ Chunking per Section
    # --------------------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""],
    )

    chunks = []

    for section_name, section_text in sections:

        if section_name == "unknown":
            section_name = "body"

        raw_chunks = splitter.split_text(section_text)

        for raw in raw_chunks:
            cleaned = raw.strip()

            # Skip tiny fragments
            if len(cleaned) < 60:
                continue

            # ✅ FIXED OWNER HANDLING
            owner_value = (
                str(document["owner"])
                if document.get("owner")
                else GLOBAL_OWNER
            )

            chunks.append(
                Document(
                    page_content=cleaned,
                    metadata={
                        "metadata_id": str(document["_id"]),
                        "user_id": owner_value,
                        "section": section_name,
                    },
                )
            )

    # --------------------------------------------------
    # 🧠 Add to Vector Store
    # --------------------------------------------------

    if chunks:
        add_chunks_to_chroma(chunks, str(document["_id"]))

    # --------------------------------------------------
    # ✅ Mark Indexed
    # --------------------------------------------------

    await db.documents.update_one(
        {"_id": document["_id"]},
        {
            "$set": {
                "indexed": True,
                "ready_for_chat": True,
                "processing": False
            }
        },
    )