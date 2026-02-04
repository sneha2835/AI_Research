import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { pdfAPI, papersAPI } from "../services/api";

import ArxivSearch from "./ArxivSearch";
import RecentPapers from "./RecentPapers";

import "./common.css";
import "./Dashboard.css";

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const fileInputRef = useRef(null);
  const librarySectionRef = useRef(null);

  const [files, setFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  const [searchDraft, setSearchDraft] = useState("");
  const [libraryFilter, setLibraryFilter] = useState("");

  // ==================================================
  // 📥 Load uploaded PDFs
  // ==================================================
  useEffect(() => {
    loadUploads();
  }, []);

  const loadUploads = async () => {
    try {
      const res = await pdfAPI.getMyUploads();

      const normalized = (res.data.documents || []).map((doc) => ({
        document_id: doc._id,
        title: doc.title,
        source: doc.source,
        size_bytes: doc.size_bytes || 0,
        uploaded_at: doc.uploaded_at || doc.created_at,
      }));

      setFiles(normalized);
    } catch (err) {
      console.error("Failed to load uploads", err);
      setFiles([]);
    } finally {
      setIsLoading(false);
    }
  };

  // ==================================================
  // 📤 Upload PDF
  // ==================================================
  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Only PDF files are supported");
      return;
    }

    setIsUploading(true);
    setUploadError("");

    try {
      await pdfAPI.upload(file);
      await loadUploads();
      e.target.value = "";
    } catch (err) {
      setUploadError("Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  const triggerFilePicker = () => {
    if (!isUploading) {
      fileInputRef.current?.click();
    }
  };

  // ==================================================
  // 🧠 Navigation
  // ==================================================
  const openChat = (document_id, title) => {
    navigate(`/chat/${document_id}`, {
      state: { title },
    });
  };

  const analyzeArxivPaper = async (paperId) => {
    const res = await papersAPI.analyzePaper(paperId);
    openChat(res.data.document_id);
  };

  // ==================================================
  // 🔍 Library filtering
  // ==================================================
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setLibraryFilter(searchDraft.trim());
  };

  const clearFilter = () => {
    setLibraryFilter("");
    setSearchDraft("");
  };

  const filteredFiles = useMemo(() => {
    if (!libraryFilter) return files;
    return files.filter((f) =>
      f.title.toLowerCase().includes(libraryFilter.toLowerCase())
    );
  }, [files, libraryFilter]);

  // ==================================================
  // 📊 Stats
  // ==================================================
  const stats = useMemo(() => {
    const totalBytes = files.reduce((s, f) => s + f.size_bytes, 0);
    return {
      count: files.length,
      totalSizeMB: totalBytes / (1024 * 1024),
    };
  }, [files]);

  const userInitials = useMemo(() => {
    if (!user?.name) return "U";
    return user.name
      .split(" ")
      .map((p) => p[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();
  }, [user?.name]);

  // ==================================================
  // 🧱 UI
  // ==================================================
  return (
    <div className="dashboard">
      <nav className="navbar">
        <div className="navbar-left">
          <button className="navbar-title" onClick={() => navigate("/")}>
            Research AI Companion
          </button>
          <p className="navbar-subtitle">
            Discover papers. Ask questions. Get clarity.
          </p>
        </div>

        <div className="navbar-right">
          <div className="user-chip">
            <span className="user-avatar">{userInitials}</span>
            <div className="user-meta">
              <span className="user-greeting">Welcome back</span>
              <span className="user-name">{user?.name}</span>
            </div>
          </div>
          <button onClick={logout} className="btn-logout">
            Logout
          </button>
        </div>
      </nav>

      <div className="dashboard-content">
        {/* ================= HERO ================= */}
        <section className="dashboard-hero">
          <div className="hero-card">
            <div className="hero-content">
              <h2>Welcome back</h2>
              <p>
                Upload PDFs or explore arXiv papers and analyze them using AI.
              </p>

              <form onSubmit={handleSearchSubmit} className="hero-search">
                <input
                  type="text"
                  value={searchDraft}
                  onChange={(e) => setSearchDraft(e.target.value)}
                  placeholder="Search your library…"
                />
                <button type="submit">Search</button>
              </form>

              <div className="hero-actions">
                <button onClick={triggerFilePicker} disabled={isUploading}>
                  {isUploading ? "Uploading…" : "Upload PDF"}
                </button>
                <button
                  onClick={() =>
                    librarySectionRef.current?.scrollIntoView({
                      behavior: "smooth",
                    })
                  }
                >
                  Browse library
                </button>
              </div>
            </div>
          </div>

          <aside className="hero-sidecard">
            <h3>Workspace</h3>
            <ul>
              <li>
                <strong>{stats.count}</strong>
                <span>PDFs</span>
              </li>
              <li>
                <strong>{stats.totalSizeMB.toFixed(2)} MB</strong>
                <span>Storage</span>
              </li>
            </ul>
          </aside>
        </section>

        {/* ================= ARXIV ================= */}
        <section className="panel-card">
          <h2>🔍 Search arXiv</h2>
          <ArxivSearch onAnalyze={analyzeArxivPaper} />
        </section>

        <section className="panel-card">
          <RecentPapers onAnalyze={analyzeArxivPaper} />
        </section>

        {/* ================= UPLOAD ================= */}
        <section className="panel-card">
          <h2>Upload PDF</h2>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            hidden
          />
          <button onClick={triggerFilePicker} disabled={isUploading}>
            Browse files
          </button>
          {uploadError && <p className="error-message">{uploadError}</p>}
        </section>

        {/* ================= LIBRARY ================= */}
        <section
          ref={librarySectionRef}
          className="panel-card"
          id="my-library"
        >
          <div className="panel-heading">
            <h2>My Library</h2>
            {libraryFilter && (
              <button onClick={clearFilter}>Clear filter</button>
            )}
          </div>

          {isLoading ? (
            <p>Loading…</p>
          ) : filteredFiles.length === 0 ? (
            <p>No documents found.</p>
          ) : (
            <div className="files-grid">
              {filteredFiles.map((file) => (
                <div key={file.document_id} className="file-card">
                  <h3>{file.title}</h3>
                  <div className="file-meta">
                    <span>
                      {(file.size_bytes / 1024 / 1024).toFixed(2)} MB
                    </span>
                  </div>
                  <button
                    className="btn-chat"
                    onClick={() => openChat(file.document_id, file.title)}
                  >
                    Open chat
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

export default Dashboard;
