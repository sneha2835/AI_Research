import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { pdfAPI, papersAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import ArxivSearch from './ArxivSearch';
import RecentPapers from './RecentPapers';
import PaperDetails from './PaperDetails';
import './common.css';
import './Dashboard.css';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // -----------------------------
  // Uploads (PDF library)
  // -----------------------------
  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [isLoadingLibrary, setIsLoadingLibrary] = useState(true);

  // -----------------------------
  // arXiv + views
  // -----------------------------
  const [recentArxiv, setRecentArxiv] = useState([]);
  const [recentlyViewed, setRecentlyViewed] = useState([]);

  // -----------------------------
  // UI state
  // -----------------------------
  const [selectedPaperId, setSelectedPaperId] = useState(null);
  const [showPaperDetail, setShowPaperDetail] = useState(false);
  const [searchDraft, setSearchDraft] = useState('');
  const [libraryFilter, setLibraryFilter] = useState('');

  const fileInputRef = useRef(null);
  const librarySectionRef = useRef(null);

  // ==================================================
  // 📥 Initial data load
  // ==================================================

  useEffect(() => {
    fetchUploads();
    fetchRecentArxiv();
    fetchRecentlyViewed();
  }, []);

  const fetchUploads = async () => {
    try {
      const res = await pdfAPI.getMyUploads();
      setFiles(res.data || []);
    } catch (err) {
      setFiles([]);
    } finally {
      setIsLoadingLibrary(false);
    }
  };

  const fetchRecentArxiv = async () => {
    try {
      const res = await papersAPI.getRecent(10);
      setRecentArxiv(res.data || []);
    } catch {
      setRecentArxiv([]);
    }
  };

  const fetchRecentlyViewed = async () => {
    try {
      const res = await papersAPI.getRecentlyViewed(10);
      setRecentlyViewed(res.data || []);
    } catch {
      setRecentlyViewed([]);
    }
  };

  // ==================================================
  // 📤 Upload PDF
  // ==================================================

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadError('Only PDF files are supported');
      return;
    }

    setIsUploading(true);
    setUploadError('');

    try {
      await pdfAPI.upload(file);
      await fetchUploads();
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  // ==================================================
  // 🧭 Navigation helpers
  // ==================================================

  const openChat = (documentId, filename) => {
    navigate(`/chat/${documentId}`, { state: { filename } });
  };

  const openPaperDetails = (paperId) => {
    setSelectedPaperId(paperId);
    setShowPaperDetail(true);
  };

  const backFromPaper = () => {
    setSelectedPaperId(null);
    setShowPaperDetail(false);
    fetchRecentlyViewed();
  };

  // ==================================================
  // 🔍 Library filtering
  // ==================================================

  const filteredFiles = useMemo(() => {
    if (!libraryFilter) return files;
    return files.filter((f) =>
      f.title?.toLowerCase().includes(libraryFilter.toLowerCase())
    );
  }, [files, libraryFilter]);

  // ==================================================
  // 👤 User display helpers
  // ==================================================

  const primaryName = user?.name?.split(' ')[0] || 'Researcher';
  const userInitials =
    user?.name
      ?.split(' ')
      .map((p) => p[0])
      .join('')
      .slice(0, 2)
      .toUpperCase() || 'U';

  // ==================================================
  // 🧩 Render
  // ==================================================

  return (
    <div className="dashboard">
      <nav className="navbar">
        <div className="navbar-left">
          <button className="navbar-title" onClick={() => navigate('/')}>
            Research AI Companion
          </button>
          <p className="navbar-subtitle">
            Discover, analyze, and chat with research papers.
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
        {/* ================================================= */}
        {/* 📄 Paper detail view */}
        {/* ================================================= */}
        {showPaperDetail && selectedPaperId ? (
          <PaperDetails
            paperId={selectedPaperId}
            onBack={backFromPaper}
          />
        ) : (
          <>
            {/* ================================================= */}
            {/* 🔥 Recent arXiv papers */}
            {/* ================================================= */}
            <section className="panel-card">
              <h2>🔥 Recent arXiv Papers</h2>
              <RecentPapers
                papers={recentArxiv}
                onSelect={openPaperDetails}
              />
            </section>

            {/* ================================================= */}
            {/* 🔍 Semantic search */}
            {/* ================================================= */}
            <section className="panel-card arxiv-search-section">
              <h2>🔍 Search arXiv</h2>
              <ArxivSearch onSelectPaper={openPaperDetails} />
            </section>

            {/* ================================================= */}
            {/* 🕘 Recently viewed (mixed) */}
            {/* ================================================= */}
            <section className="panel-card">
              <h2>🕘 Recently Viewed</h2>
              <RecentPapers
                papers={recentlyViewed}
                onSelect={(item) => {
                  if (item.document_id) {
                    openChat(item.document_id);
                  } else if (item._id) {
                    openPaperDetails(item._id);
                  }
                }}
              />
            </section>

            {/* ================================================= */}
            {/* 📤 Upload + library */}
            {/* ================================================= */}
            <section ref={librarySectionRef} className="panel-card">
              <h2>📚 My Library</h2>

              <div className="library-actions">
                <input
                  type="text"
                  placeholder="Search your PDFs…"
                  value={searchDraft}
                  onChange={(e) => setSearchDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      setLibraryFilter(searchDraft);
                    }
                  }}
                />

                <button onClick={() => fileInputRef.current?.click()}>
                  Upload PDF
                </button>

                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  hidden
                  onChange={handleFileUpload}
                />
              </div>

              {uploadError && <p className="error-message">{uploadError}</p>}

              {isLoadingLibrary ? (
                <p>Loading library…</p>
              ) : filteredFiles.length === 0 ? (
                <p>No PDFs found.</p>
              ) : (
                <div className="files-grid">
                  {filteredFiles.map((file) => (
                    <div key={file._id} className="file-card">
                      <h3>{file.title}</h3>
                      <button
                        onClick={() =>
                          openChat(file._id, file.title)
                        }
                      >
                        Open chat
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
