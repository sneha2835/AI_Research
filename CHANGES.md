# Recent Changes Summary

## 🚀 Quick Start Commands

### Backend
```bash
cd AI_Research
.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8001
```

### Frontend
```bash
cd AI_Research\frontend
npm run dev
```

## 🔧 Major Changes

### API & Backend Fixes
- **CORS Configuration**: Set `allow_origins=["*"]` for development testing
- **Port Standardization**: Backend running on port **8001** (updated frontend API calls)
- **New Endpoints Added**:
  - `GET /pdf/my_uploads` - Fetch user's uploaded PDFs
  - `DELETE /pdf/delete/{document_id}` - Delete PDF documents
  - `GET /pdf/extract_chunks/{document_id}` - Retrieve document chunks

### Data & Schema Fixes
- **Field Mapping**: Fixed `metadata_id` vs `document_id` inconsistency across frontend/backend
- **File Size Tracking**: Added `size_bytes` calculation during PDF upload (fixes 0.00 MB display)
- **Document Response**: Added `metadata_id` field to `/pdf/my_uploads` response for frontend compatibility

### Frontend Improvements
- **Error Handling**: Improved Chat component error handling (fixes React "invalid object" errors)
- **API Service**: Updated `askWithHistory()` to send correct `document_id` field
- **List Keys**: Added React keys to Dashboard stat cards (removes console warnings)

### AI/LLM Enhancements
- **Prompt Optimization**: Simplified Q&A prompt for more helpful responses (less conservative)
- **Debug Logging**: Added chunk retrieval logging (`🔍 Query` and `✅ Valid chunks` messages)
- **Search Error Handling**: Added try-catch for ChromaDB search failures

### Database & Storage
- **ChromaDB Reset**: Cleaned `chroma_persist/` directory to fix embedding dimension mismatch (384 vs 768)
- **Collection Recreation**: Fresh ChromaDB collections with correct BAAI/bge-base-en-v1.5 embeddings

## 📋 Key Files Modified

- `backend/app/main.py` - CORS middleware configuration
- `backend/routers/pdf_chunking.py` - Added endpoints, file size tracking, improved prompts
- `backend/routers/papers.py` - Added error handling for search
- `frontend/src/services/api.js` - Fixed field names, updated port
- `frontend/src/components/Dashboard.jsx` - Fixed error handling, added keys
- `frontend/src/components/Chat.jsx` - Improved error message handling

## ✅ Current Status

- Backend: Running on `http://0.0.0.0:8001`
- Frontend: Running on `http://localhost:5173`
- All CRUD operations functional (Create, Read, Update, Delete PDFs)
- PDF upload, chat, and search features working
- User management admin panel operational
