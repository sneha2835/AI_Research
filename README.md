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

## Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.10+** - [Download Python](https://www.python.org/downloads/)
2. **uv** (Fast Python package installer) - [Install uv](https://github.com/astral-sh/uv)
   ```powershell
   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
3. **Docker Desktop** - [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
4. **Git** - [Download Git](https://git-scm.com/downloads)

## Quick Start

### Step 1: Clone the Repository

```powershell
git clone <repository-url>
cd AI_Research
```

### Step 2: Initialize uv and Create Virtual Environment

```powershell
# Initialize uv project
uv init

# Create virtual environment
uv venv

# Install dependencies
uv pip install -r requirements.txt
```

### Step 3: Set Up Environment Variables

The `.env` file should already exist. Verify it contains:

```env
# MongoDB Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=research_db

# JWT Configuration
SECRET_KEY=your-secret-key-change-in-production-with-strong-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Chroma Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000

# GROBID Configuration
GROBID_URL=http://localhost:8070

# Ollama Configuration
OLLAMA_URL=http://localhost:11434
```

### Step 4: Install and Start Docker Desktop

1. **Install Docker Desktop** from [docker.com](https://www.docker.com/products/docker-desktop/)
2. **Launch Docker Desktop** from Start Menu
3. **Wait** until Docker Desktop shows "Engine running" in the bottom-left corner
4. If you see "WSL needs updating" error:
   ```powershell
   # Update WSL
   wsl --update
   
   # Shutdown WSL
   wsl --shutdown
   
   # Restart Docker Desktop
   ```

### Step 5: Start Docker Services

```powershell
# Start all services (MongoDB, ChromaDB, GROBID, Ollama)
docker-compose up -d

# Verify services are running
docker ps
```

You should see 4 containers running:
- `research_mongodb` (port 27017)
- `research_chromadb` (port 8000)
- `research_grobid` (port 8070)
- `research_ollama` (port 11434)

### Step 6: Start the Backend Server

```powershell
# Start server
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8001
```

The backend will be running at: **http://localhost:8001**

### Step 7: Test the API

Open your browser and navigate to:
- **API Documentation:** http://localhost:8001/docs
- **Health Check:** http://localhost:8001/health

## Using the API

### Quick Test Flow:

1. **Register a User** - Go to http://localhost:8001/docs, click `POST /register`
2. **Login** - Click `POST /token`, copy the `access_token`
3. **Authorize** - Click "Authorize" button at top, paste token
4. **Upload a PDF** - Click `POST /pdf/upload`, choose file
5. **Extract Chunks** - Click `GET /pdf/extract_chunks/{metadata_id}` with your metadata_id
6. **Semantic Search** - Click `GET /pdf/search`, enter a query
7. **Ask Questions** - Click `GET /pdf/ask`, enter a question about your PDF

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /token` - Login and get JWT token
- `GET /users/me` - Get current user info

### PDF Management
- `POST /pdf/upload` - Upload PDF file
- `GET /pdf/my_uploads` - List user's uploaded PDFs
- `GET /pdf/download/{metadata_id}` - Download PDF
- `DELETE /pdf/delete/{metadata_id}` - Delete PDF

### RAG Features
- `GET /pdf/extract_chunks/{metadata_id}` - Extract and store PDF chunks
- `GET /pdf/search` - Semantic search across PDFs
- `GET /pdf/ask` - Ask questions (RAG)
- `POST /pdf/chat` - Chat with follow-up questions
- `POST /pdf/summarize` - Summarize text

## Troubleshooting

### Docker Issues
- **Error: "cannot connect to Docker daemon"** - Ensure Docker Desktop is running
- Check system tray for Docker icon

### Port Already in Use
```powershell
# Find and kill the process using port 8001
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

## Development Commands

```powershell
# Stop backend: Press CTRL+C in terminal

# Stop Docker services
docker-compose down

# View logs
docker-compose logs -f

# Reset everything
docker-compose down -v
```
