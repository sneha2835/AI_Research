# Research AI Companion

A local-first, privacy-preserving AI assistant for scientific papers. Upload PDFs, chat with papers, summarize, annotate, manage citations, and get recommendations—fully offline and open-source.

## Tech Stack

- **Backend:** FastAPI (Python), MongoDB, Chroma, GROBID, Ollama
- **Frontend:** React (Vite+TypeScript), Tailwind CSS, PDF.js
- **AI Models:** phi-3, llama3, scibert, bge/specter2 for embeddings

## Project Structure

research/
├── backend/
├── frontend/
├── models/
├── vector_db/
├── grobid/
├── docker-compose.yml
├── .env


## Features

- Secure user authentication
- PDF upload, parsing, and semantic search
- Instant AI summary & RAG “Ask This Paper” chat
- Named entity recognition, citation extraction/export
- Research recommendations
- Local, containerized deployment (Docker)

## Quick Start

TBA...
