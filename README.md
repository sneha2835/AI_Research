

# 🧠 AI Research Companion

AI-powered research assistant for scientific literature review, PDF analysis, and grounded Q&A with citation support.

---

## 🚀 Features

* 🔐 JWT Authentication (Email/Password)
* 🔑 Google OAuth Login
* 📄 PDF Upload & Processing
* 🔎 arXiv Paper Search
* 💬 Context-Grounded Q&A
* 📊 Dashboard with Usage Stats
* 📚 Persistent Chat History
* 🧠 Vector Search (ChromaDB)
* 🗂 MongoDB Backend
* 🎨 React + Vite Frontend

---

# 🏗 Architecture

```
Frontend (React + Vite)
        ↓
FastAPI Backend
        ↓
MongoDB (Users, Chat, Metadata)
        ↓
ChromaDB (Vector Storage)
        ↓
Transformers (LLM + Embeddings)
```

---

# 📦 Tech Stack

## 🖥 Backend

* FastAPI
* MongoDB (Motor async)
* ChromaDB
* Transformers
* Sentence Transformers
* Argon2 Password Hashing
* JWT (python-jose)
* Google OAuth

## 🌐 Frontend

* React 19
* Vite
* React Router
* Axios
* jsPDF
* Framer Motion

---

# 🛠 Installation Guide

---

# 🔹 1️⃣ Clone the Repository

```bash
git clone https://github.com/sneha2835/AI_Research.git
cd AI_Research
git checkout resolve_f
```

---

# 🖥 Backend Setup

---

## 🔹 2️⃣ Create Virtual Environment

```bash
cd backend
python -m venv venv
```

### Activate

**Windows**

```bash
venv\Scripts\activate
```

**Mac/Linux**

```bash
source venv/bin/activate
```

---

## 🔹 3️⃣ Install Backend Dependencies

```bash
pip install -r requirements_backend.txt
```

---

## 🔹 4️⃣ Backend Environment Variables

Create this file:

```
backend/.env
```

Add:

```
MONGO_URL=your_mongodb_connection_string
DB_NAME=ai_research

JWT_SECRET=your_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/auth/google/callback

FRONTEND_URL=http://localhost:5173
```

---

## 🔹 5️⃣ Run Backend

```bash
uvicorn app.main:app --reload
```

Backend runs at:

```
http://127.0.0.1:8000
```

Swagger docs:

```
http://127.0.0.1:8000/docs
```

---

# 🌐 Frontend Setup

---

## 🔹 6️⃣ Install Frontend Dependencies

Open a new terminal:

```bash
cd frontend
npm install
```

---

## 🔹 7️⃣ Frontend Environment Variables

Create this file:

```
frontend/.env
```

Add:

```
VITE_API_BASE_URL=http://localhost:8000
```

⚠ Important: All Vite environment variables must start with `VITE_`

---

## 🔹 8️⃣ Run Frontend

```bash
npm run dev
```

Frontend runs at:

```
http://localhost:5173
```

---

# 🔐 Google OAuth Setup

1. Go to Google Cloud Console
2. Create OAuth 2.0 Client ID
3. Add Authorized Redirect URI:

```
http://127.0.0.1:8000/auth/google/callback
```

4. Add the credentials inside:

```
backend/.env
```

---

# 📂 Project Structure

```
AI_Research/
│
├── backend/
│   ├── app/
│   ├── routers/
│   ├── services/
│   ├── requirements_backend.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   └── .env
│
└── README.md
```

---

# 🧪 Development Workflow

### Start Backend

```bash
cd backend
uvicorn app.main:app --reload
```

### Start Frontend

```bash
cd frontend
npm run dev
```

---

# 📌 Current Status

✅ Authentication complete
✅ Google OAuth integrated
✅ Vector search working
✅ Chat persistence implemented
✅ PDF + arXiv ingestion working

🚧 Hybrid retrieval (planned)
🚧 Cross-encoder reranking (planned)
🚧 Structured citation engine (planned)

---

# 🧠 Roadmap

* Hybrid Retrieval (BM25 + Semantic)
* Cross-Encoder Reranking
* Structured Citation Engine
* Section-Aware Summarization
* Hierarchical Summarization
* Dockerized Deployment

---
🎥 Demo

Project demo video available inside:

frontend/public/Major_Proj_Demo.mp4
---

