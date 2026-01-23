# backend/routers/pdf_chunking.py

from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from backend.app.db import db
from backend.app.auth import get_current_user
from backend.app.chroma_store import semantic_search
from backend.services.pdf_service import extract_and_index_pdf
from backend.app.llm_inference import answer_from_context, summarize_text
from backend.schemas.pdf import AskPdfRequest, SummarizePdfRequest
from backend.services.document_service import create_uploaded_document
from backend.services.retrieval_service import bm25_search, hybrid_merge
from backend.services.reranker_service import rerank_chunks

import os
import re

pdf_router = APIRouter(prefix="/pdf", tags=["PDF"])

UPLOAD_DIR = "backend/pdf_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ==================================================
# 🔧 HELPER FUNCTIONS
# ==================================================

def is_junk_chunk(text: str) -> bool:
    text = text.strip()
    if len(text) < 30:
        return True
    if re.fullmatch(r"\[\d+\]", text):
        return True
    return False


def deduplicate_chunks(chunks, max_chunks):
    seen = set()
    unique = []

    for c in chunks:
        key = c.page_content.strip()[:200]
        if key not in seen:
            seen.add(key)
            unique.append(c)
        if len(unique) >= max_chunks:
            break

    return unique

def is_definition_query(query: str) -> bool:
    query = query.lower()
    return any(
        phrase in query
        for phrase in [
            "what is",
            "define",
            "definition of",
            "meaning of",
        ]
    )

# ==================================================
# 📤 Upload PDF
# ==================================================

@pdf_router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are allowed")

    document = await create_uploaded_document(
    filename=file.filename,
    user_id=current_user["_id"],
)


    path = os.path.join(UPLOAD_DIR, f"{document['_id']}.pdf")

    with open(path, "wb") as f:
        f.write(await file.read())

    await db.documents.update_one(
        {"_id": document["_id"]},
        {"$set": {"path": path}},
    )

    if not document.get("indexed"):
        await extract_and_index_pdf({
            "_id": document["_id"],
            "path": path,
            "owner": current_user["_id"],
        })


    return {
        "document_id": str(document["_id"]),
        "status": "uploaded",
    }


# ==================================================
# ❓ Ask PDF (Q&A) + CHAT HISTORY
# ==================================================

@pdf_router.post("/ask")
async def ask_pdf(
    payload: AskPdfRequest,
    current_user=Depends(get_current_user),
):
    # -------------------------
    # 1️⃣ Validate access
    # -------------------------
    if not ObjectId.is_valid(payload.document_id):
        raise HTTPException(400, "Invalid document id")

    document = await db.documents.find_one({
        "_id": ObjectId(payload.document_id),
        "$or": [
            {"owner": current_user["_id"]},
            {"owner": None},
        ],
    })

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    source = "arxiv" if document.get("source") == "arxiv" else "upload"

    # -------------------------
    # 🕘 Log recent view (uploads only)
    # -------------------------
    if source == "upload":
        await db.recent_views.update_one(
            {
                "user_id": current_user["_id"],
                "type": "upload",
                "document_id": ObjectId(payload.document_id),
            },
            {
                "$set": {
                    "title": document.get("title"),
                    "viewed_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )

    # ==================================================
    # 🔍 HYBRID RETRIEVAL (Semantic + BM25)
    # ==================================================

    # 2️⃣ Semantic retrieval (candidate pool)
    semantic_chunks = semantic_search(
        query=payload.query,
        n_results=30,
        metadata_id=payload.document_id,
        user_id=document.get("owner") if source == "upload" else None,
        section_priority=not is_definition_query(payload.query),
    )

    # 3️⃣ Filter junk / empty chunks
    semantic_chunks = [
        c for c in semantic_chunks
        if getattr(c, "page_content", "").strip()
        and not is_junk_chunk(c.page_content)
    ]

    if not semantic_chunks:
        answer = "No relevant content found in this document."

    else:
        texts = [c.page_content for c in semantic_chunks]

        # 4️⃣ BM25 lexical retrieval
        bm25_ranked = bm25_search(
            query=payload.query,
            documents=texts,
            top_k=min(30, len(texts)),
        )

        bm25_indices = [idx for idx, _ in bm25_ranked]
        bm25_scores = [score for _, score in bm25_ranked]

        # 5️⃣ Semantic scores (rank-based proxy)
        semantic_scores = list(
            range(len(semantic_chunks), 0, -1)
        )

        # 6️⃣ Hybrid merge
        merged = hybrid_merge(
            semantic_docs=semantic_chunks,
            semantic_scores=semantic_scores,
            bm25_indices=bm25_indices,
            bm25_scores=bm25_scores,
            alpha=0.6,  # semantic-heavy
        )

        # 7️⃣ Final top-K chunks
        # 7️⃣ Take more candidates before reranking
        candidate_chunks = [
            item["doc"]
            for item in merged[:20]
        ]

        # 8️⃣ Cross-encoder reranking (🔥 key step)
        final_chunks = rerank_chunks(
            query=payload.query,
            chunks=candidate_chunks,
            top_k=payload.n_results,
)


        final_chunks = deduplicate_chunks(
            final_chunks,
            payload.n_results,
        )

        if not final_chunks:
            answer = "No relevant content found in this document."
        else:
            context = "\n\n".join(
                c.page_content for c in final_chunks
            )[:3500]

            prompt = f"""
You are an expert academic research assistant.

Answer the question strictly using the context below.
If the answer is not explicitly stated, say:
"The paper does not explicitly state this."

Context:
{context}

Question:
{payload.query}

Answer in clear academic English (4–6 sentences):
""".strip()

            answer = (
                answer_from_context(prompt)
                or "The paper does not explicitly state this."
            )

    # ==================================================
    # 💾 Save chat history (unchanged)
    # ==================================================
    timestamp = datetime.utcnow()

    await db.chat_history.insert_many([
        {
            "document_id": ObjectId(payload.document_id),
            "user_id": current_user["_id"],
            "role": "user",
            "type": "qa",
            "content": payload.query,
            "source": source,
            "timestamp": timestamp,
        },
        {
            "document_id": ObjectId(payload.document_id),
            "user_id": current_user["_id"],
            "role": "assistant",
            "type": "qa",
            "content": answer,
            "source": source,
            "timestamp": timestamp,
        },
    ])

    return {"answer": answer}

# ==================================================
# 📝 Summarize PDF
# ==================================================


@pdf_router.post("/summarize")
async def summarize_pdf(
    payload: SummarizePdfRequest,
    current_user=Depends(get_current_user),
):
    # -------------------------
    # 1️⃣ Validate document access
    # -------------------------
    if not ObjectId.is_valid(payload.document_id):
        raise HTTPException(400, "Invalid document id")

    document = await db.documents.find_one({
        "_id": ObjectId(payload.document_id),
        "$or": [
            {"owner": current_user["_id"]},
            {"owner": None},
        ],
    })

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    source = "arxiv" if document.get("source") == "arxiv" else "upload"

    # -------------------------
    # 🕘 Log recent view (uploads only)
    # -------------------------
    if source == "upload":
        await db.recent_views.update_one(
            {
                "user_id": current_user["_id"],
                "type": "upload",
                "document_id": ObjectId(payload.document_id),
            },
            {
                "$set": {
                    "title": document.get("title"),
                    "viewed_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )

    # ==================================================
    # 🔍 RETRIEVAL FOR SUMMARIZATION
    # ==================================================
    semantic_chunks = semantic_search(
        query="Summarize the main contributions and findings of this paper",
        n_results=40,
        metadata_id=payload.document_id,
        user_id=document.get("owner") if source == "upload" else None,
        section_priority=False,
    )

    semantic_chunks = [
        c for c in semantic_chunks
        if getattr(c, "page_content", "").strip()
        and not is_junk_chunk(c.page_content)
    ]

    if not semantic_chunks:
        return {"summary": "No readable content found in this document."}

    # ==================================================
    # 🔁 Cross-encoder reranking (🔥 key)
    # ==================================================
    reranked_chunks = rerank_chunks(
        query="Summarize the main contributions and findings of this paper",
        chunks=semantic_chunks,
        top_k=20,
    )

    # ==================================================
    # 📚 Group chunks by section
    # ==================================================
    sections = {
        "definition": [],
        "abstract": [],
        "introduction": [],
        "body": [],
        "conclusion": [],
    }

    for c in reranked_chunks:
        sec = c.metadata.get("section", "body")
        if sec in sections:
            sections[sec].append(c.page_content)
        else:
            sections["body"].append(c.page_content)

    # ==================================================
    # 🧠 SECTION-WISE SUMMARIZATION
    # ==================================================
    section_summaries = {}

    for section, texts in sections.items():
        if not texts:
            continue

        section_context = "\n\n".join(texts)[:3000]

        section_prompt = f"""
Summarize the following section of an academic paper.

Section: {section}

Text:
{section_context}

Write a concise academic summary (3–5 sentences).
""".strip()

        section_summary = summarize_text(section_prompt)
        if section_summary:
            section_summaries[section] = section_summary.strip()

    # ==================================================
    # 🧩 FINAL MERGE SUMMARY
    # ==================================================
    final_prompt = f"""
You are an expert academic summarizer.

Merge the following section summaries into a single coherent paper summary.

Format:
Objective:
Problem Statement:
Methodology:
Key Findings:
Conclusion:

Section Summaries:
{section_summaries}
""".strip()

    summary = summarize_text(final_prompt)

    if not summary or not summary.strip():
        summary = (
            "Objective:\nNot clearly stated.\n\n"
            "Problem Statement:\nNot clearly stated.\n\n"
            "Methodology:\nNot clearly stated.\n\n"
            "Key Findings:\nNot clearly stated.\n\n"
            "Conclusion:\nNot clearly stated."
        )

    # ==================================================
    # 💾 Save summary to chat history
    # ==================================================
    await db.chat_history.insert_one({
        "document_id": ObjectId(payload.document_id),
        "user_id": current_user["_id"],
        "role": "assistant",
        "type": "summary",
        "content": summary,
        "source": source,
        "timestamp": datetime.utcnow(),
    })

    return {"summary": summary}

