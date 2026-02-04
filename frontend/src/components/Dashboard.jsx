import React, { useState, useEffect, useMemo, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import { pdfAPI, papersAPI } from "../services/api";
import { useNavigate } from "react-router-dom";
import ArxivSearch from "./ArxivSearch";
import RecentPapers from "./RecentPapers";
import "./common.css";
import "./Dashboard.css";

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const fileInputRef = useRef(null);
  const librarySectionRef = useRef(null);

  const [searchDraft, setSearchDraft] = useState("");
  const [libraryFilter, setLibraryFilter] = useState("");

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      const res = await pdfAPI.getMyUploads();
      setFiles(res.data);
    } catch (err) {
      console.error("Failed to fetch uploads", err);
      setFiles([]);
    } finally {
      setIsLoading(false);
    }
  };

  // ================= Upload =================

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
      await fetchFiles();
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

  // ================= Navigation =================

  const handleChat = (documentId) => {
    navigate(`/chat/${documentId}`);
  };

  const handleDelete = async (documentId) => {
    if (!confirm("Delete this PDF?")) return;

    try {
      await pdfAPI.deletePDF(documentId);
      await fetchFiles();
    } catch {
      alert("Delete failed");
    }
  };

  const handleProcessArxivPaper = async (paperId) => {
    try {
      const res = await papersAPI.analyzePaper(paperId);
      navigate(`/chat/${res.data.document_id}`);
    } catch (err) {
      alert("Failed to analyze paper");
    }
  };

  // ================= Derived UI =================

  const filteredFiles = useMemo(() => {
    if (!libraryFilter) return files;
    return files.filter((f) =>
      f.title.toLowerCase().includes(libraryFilter.toLowerCase())
    );
  }, [files, libraryFilter]);

  const stats = useMemo(() => {
    const count = files.length;
    const totalBytes = files.reduce(
      (sum, f) => sum + (f.size_bytes || 0),
      0
    );
    return {
      count,
      totalSizeMB: totalBytes / (1024 * 1024),
    };
  }, [files]);

  const primaryName = user?.name?.split(" ")[0] || "Researcher";

  // ================= Render =================

  return (
    <div className="dashboard">
      <nav className="navbar">
        <div className="navbar-left">
          <h1>Research AI Companion</h1>
          <p>Organize papers, uncover insights.</p>
        </div>
        <div className="navbar-right">
          <span>{user?.name}</span>
          <button onClick={logout}>Logout</button>
        </div>
      </nav>

      <section className="dashboard-hero">
        <h2>Welcome back, {primaryName}</h2>
        <p>Search arXiv or upload your PDFs to start chatting.</p>

        <div className="hero-actions">
          <button onClick={triggerFilePicker} disabled={isUploading}>
            {isUploading ? "Uploading…" : "Upload PDF"}
          </button>
          <button onClick={() => librarySectionRef.current?.scrollIntoView({ behavior: "smooth" })}>
            Browse Library
          </button>
        </div>
      </section>

      {/* 🔍 arXiv Search */}
      <section className="arxiv-search-section">
        <h2>Search arXiv</h2>
        <ArxivSearch
          onSelectPaper={(paper) => handleProcessArxivPaper(paper._id)}
        />
      </section>

      {/* 📚 Library */}
      <section ref={librarySectionRef} className="files-section">
        <h2>My Library</h2>

        <input
          type="text"
          placeholder="Search library…"
          value={searchDraft}
          onChange={(e) => setSearchDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && setLibraryFilter(searchDraft)}
        />

        {isLoading ? (
          <p>Loading…</p>
        ) : filteredFiles.length === 0 ? (
          <p>No PDFs found.</p>
        ) : (
          <div className="files-grid">
            {filteredFiles.map((file) => (
              <div key={file._id} className="file-card">
                <h3>{file.title}</h3>
                <div className="file-meta">
                  <span>{file.source === "arxiv" ? "arXiv" : "Upload"}</span>
                </div>
                <div className="file-actions">
                  <button onClick={() => handleChat(file._id)}>
                    {file.source === "arxiv" ? "Analyze" : "Open Chat"}
                  </button>
                  {file.source === "upload" && (
                    <button onClick={() => handleDelete(file._id)}>Delete</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 📤 Hidden upload input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        onChange={handleFileUpload}
        hidden
      />
    </div>
  );
};

export default Dashboard;
