# backend/routers/papers.py

import aiohttp
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.db import db
from backend.app.auth import get_current_user
from backend.app.chroma_store import search_research_papers
from backend.services.document_service import get_or_create_arxiv_document
from backend.services.pdf_service import extract_and_index_pdf

UPLOAD_DIR = "backend/pdf_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

papers_router = APIRouter(prefix="/papers", tags=["Papers"])

async def fetch_arxiv_papers(query: str, max_results: int = 10):
    """Fetch papers directly from arXiv API"""
    base_url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            if response.status != 200:
                return []
            
            xml_data = await response.text()
            
    # Parse XML response
    root = ET.fromstring(xml_data)
    ns = {'atom': 'http://www.w3.org/2005/Atom'}
    
    papers = []
    for entry in root.findall('atom:entry', ns):
        try:
            arxiv_id = entry.find('atom:id', ns).text.split('/abs/')[-1]
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
            published = entry.find('atom:published', ns).text
            
            # Get PDF link
            pdf_link = None
            for link in entry.findall('atom:link', ns):
                if link.get('title') == 'pdf':
                    pdf_link = link.get('href')
                    break
            
            # Get categories
            categories = [cat.get('term') for cat in entry.findall('atom:category', ns)]
            
            paper_data = {
                "arxiv_id": arxiv_id,
                "title": title,
                "abstract": summary,
                "published": published,
                "pdf_url": pdf_link,
                "categories": categories,
                "source": "arxiv"
            }
            
            # Store in database
            existing = await db.research_papers.find_one({"arxiv_id": arxiv_id})
            if not existing:
                result = await db.research_papers.insert_one(paper_data)
                paper_data["_id"] = str(result.inserted_id)
            else:
                paper_data["_id"] = str(existing["_id"])
            
            papers.append(paper_data)
        except Exception as e:
            print(f"Error parsing paper: {e}")
            continue
    
    return papers

@papers_router.get("/recent")
async def get_recent_papers(
    limit: int = Query(10, ge=5, le=20),
    current_user=Depends(get_current_user),
):
    """Fetch recent papers from arXiv API"""
    papers = await fetch_arxiv_papers("machine learning OR deep learning OR artificial intelligence", limit)
    return papers

@papers_router.get("/search")
async def search_papers(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=3, le=50),
    current_user=Depends(get_current_user),
):
    """Search papers using semantic similarity via ChromaDB"""
    try:
        # Try semantic search from ChromaDB first
        results = search_research_papers(q, n_results=limit)
        
        if results:
            # Convert ChromaDB results to paper format
            papers = []
            for doc in results:
                paper_data = {
                    "arxiv_id": doc.metadata.get("arxiv_id", doc.page_content[:20]),
                    "title": doc.metadata.get("title", "Untitled"),
                    "abstract": doc.page_content,
                    "published": doc.metadata.get("published", ""),
                    "pdf_url": doc.metadata.get("pdf_url", ""),
                    "categories": doc.metadata.get("categories", []),
                    "_id": doc.metadata.get("paper_id", "")
                }
                papers.append(paper_data)
            return papers
        else:
            # Fallback to arXiv API if ChromaDB is empty
            print("⚠️ ChromaDB empty, falling back to arXiv API")
            papers = await fetch_arxiv_papers(q, limit)
            return papers
    except Exception as e:
        print(f"❌ ChromaDB search failed: {e}, falling back to arXiv API")
        papers = await fetch_arxiv_papers(q, limit)
        return papers

@papers_router.get("/{paper_id}")
async def get_paper_details(
    paper_id: str,
    current_user=Depends(get_current_user),
):
    """Get details of a specific paper"""
    if not ObjectId.is_valid(paper_id):
        raise HTTPException(400, "Invalid paper ID")
    
    paper = await db.research_papers.find_one({"_id": ObjectId(paper_id)})
    if not paper:
        raise HTTPException(404, "Paper not found")
    
    paper["_id"] = str(paper["_id"])
    return paper

@papers_router.post("/process/{paper_id}")
@papers_router.post("/analyze/{paper_id}")
async def analyze_arxiv_paper(
    paper_id: str,
    current_user=Depends(get_current_user),
):
    paper = await db.research_papers.find_one({"_id": ObjectId(paper_id)})
    if not paper:
        raise HTTPException(404, "Paper not found")

    document = await get_or_create_arxiv_document(paper)

    if not document.get("path"):
        async with aiohttp.ClientSession() as session:
            async with session.get(paper["pdf_url"]) as resp:
                if resp.status != 200:
                    raise HTTPException(500, "PDF download failed")
                data = await resp.read()

        path = os.path.join(UPLOAD_DIR, f"{document['_id']}.pdf")
        with open(path, "wb") as f:
            f.write(data)

        await db.documents.update_one(
            {"_id": document["_id"]},
            {"$set": {"path": path}},
        )
        document["path"] = path

        await extract_and_index_pdf(document)

    await db.recent_views.update_one(
        {
            "user_id": current_user["_id"],
            "document_id": str(document["_id"]),
        },
        {"$set": {"viewed_at": datetime.utcnow()}},
        upsert=True,
    )

    return {"document_id": str(document["_id"])}

@papers_router.get("/recently-viewed")
async def get_recently_viewed(
    limit: int = Query(10, ge=5, le=20),
    current_user=Depends(get_current_user),
):
    """Get recently viewed papers for the current user"""
    recent_views = await db.recent_views.find(
        {"user_id": current_user["_id"]}
    ).sort("viewed_at", -1).limit(limit).to_list(limit)
    
    result = []
    for view in recent_views:
        doc_id = view.get("document_id")
        if not doc_id or not ObjectId.is_valid(doc_id):
            continue
            
        document = await db.documents.find_one({"_id": ObjectId(doc_id)})
        if not document:
            continue
            
        item = {
            "_id": str(document["_id"]),
            "title": document.get("title", "Unknown"),
            "type": document.get("source", "upload"),
            "source": document.get("source", "upload"),
            "viewed_at": view.get("viewed_at")
        }
        
        # If it's an arXiv paper, get additional details
        if document.get("arxiv_id"):
            paper = await db.research_papers.find_one({"arxiv_id": document["arxiv_id"]})
            if paper:
                item["abstract"] = paper.get("abstract", "")
                item["published"] = paper.get("published")
                
        result.append(item)
    
    return result

