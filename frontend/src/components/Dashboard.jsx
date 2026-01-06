import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { pdfAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import './common.css';
import './Dashboard.css';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const fileInputRef = useRef(null);
  const librarySectionRef = useRef(null);
  const [searchDraft, setSearchDraft] = useState('');
  const [libraryFilter, setLibraryFilter] = useState('');

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      const response = await pdfAPI.getMyUploads();
      setFiles(response.data.files);
    } catch (error) {
      console.error('Failed to fetch files:', error);
    } finally {
      setIsLoading(false);
    }
  };

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
      await fetchFiles();
      e.target.value = '';
    } catch (error) {
      setUploadError(error.response?.data?.detail || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const triggerFilePicker = () => {
    if (!isUploading) {
      fileInputRef.current?.click();
    }
  };

  const handleNavigateHome = () => {
    navigate('/');
  };

  const handleScrollToLibrary = () => {
    librarySectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    setLibraryFilter(searchDraft.trim());
  };

  const clearFilter = () => {
    setLibraryFilter('');
    setSearchDraft('');
  };

  const handleDelete = async (metadataId) => {
    if (!confirm('Are you sure you want to delete this PDF?')) return;

    try {
      await pdfAPI.deletePDF(metadataId);
      await fetchFiles();
    } catch (error) {
      alert('Failed to delete file');
    }
  };

  const handleChat = (metadataId, filename) => {
    navigate(`/chat/${metadataId}`, { state: { filename } });
  };

  const stats = useMemo(() => {
    const count = files.length;
    const totalBytes = files.reduce((sum, file) => sum + (file.size_bytes || 0), 0);
    const latestTimestamp = files.reduce((latest, file) => {
      const nextTime = new Date(file.uploaded_at).getTime();
      return Number.isNaN(nextTime) ? latest : Math.max(latest, nextTime);
    }, 0);

    return {
      count,
      totalSizeMB: totalBytes / (1024 * 1024),
      lastUploadedAt: latestTimestamp ? new Date(latestTimestamp) : null,
    };
  }, [files]);

  const primaryName = useMemo(() => {
    if (!user?.name) return 'Researcher';
    return user.name.split(' ')[0];
  }, [user?.name]);

  const userInitials = useMemo(() => {
    if (!user?.name) return 'U';
    return user.name
      .split(' ')
      .filter(Boolean)
      .map((part) => part[0])
      .join('')
      .slice(0, 2)
      .toUpperCase();
  }, [user?.name]);

  const filteredFiles = useMemo(() => {
    if (!libraryFilter) {
      return files;
    }

    const query = libraryFilter.toLowerCase();
    return files.filter((file) => file.filename.toLowerCase().includes(query));
  }, [files, libraryFilter]);

  const recentUploads = useMemo(() => files.slice(0, 3), [files]);

  return (
    <div className="dashboard">
      <nav className="navbar">
        <div className="navbar-left">
          <button type="button" className="navbar-title" onClick={handleNavigateHome}>
            Research AI Companion
          </button>
          <p className="navbar-subtitle">Organize your papers, uncover insights, and keep progress in sight.</p>
        </div>
        <div className="navbar-right">
          <div className="user-chip">
            <span className="user-avatar">{userInitials}</span>
            <div className="user-meta">
              <span className="user-greeting">Welcome back</span>
              <span className="user-name">{user?.name || 'Guest'}</span>
            </div>
          </div>
          <button onClick={logout} className="btn-logout">Logout</button>
        </div>
      </nav>

      <div className="dashboard-content">
        <section className="dashboard-hero">
          <div className="hero-card">
            <div className="hero-illustration" aria-hidden="true">
              <span role="img" aria-label="Researching">🔎</span>
            </div>
            <div className="hero-content">
              <span className="hero-eyebrow">Workspace companion</span>
              <h2>Follow your curiosity, {primaryName}</h2>
              <p>
                Jump from questions to insights with a unified library, smart summaries, and Groq-speed document chat.
              </p>
              <form className="hero-search" onSubmit={handleSearchSubmit}>
                <label htmlFor="dashboard-search" className="sr-only">Search library</label>
                <div className="search-input">
                  <span aria-hidden="true">🔍</span>
                  <input
                    id="dashboard-search"
                    type="text"
                    value={searchDraft}
                    onChange={(event) => setSearchDraft(event.target.value)}
                    placeholder="Title, DOI, or keywords"
                  />
                </div>
                <button type="submit">Search</button>
              </form>
              <div className="hero-actions">
                <button type="button" onClick={triggerFilePicker} disabled={isUploading}>
                  {isUploading ? 'Uploading…' : 'Upload a PDF'}
                </button>
                <button type="button" onClick={handleScrollToLibrary}>
                  Browse library
                </button>
              </div>
            </div>
          </div>

          <aside className="hero-sidecard">
            <h3>Quick highlights</h3>
            <ul>
              <li>
                <strong>{stats.count}</strong>
                <span>PDFs in your workspace</span>
              </li>
              <li>
                <strong>{stats.count ? stats.totalSizeMB.toFixed(2) : '0.00'} MB</strong>
                <span>Total storage used</span>
              </li>
              <li>
                <strong>
                  {stats.lastUploadedAt ? stats.lastUploadedAt.toLocaleDateString() : 'No uploads yet'}
                </strong>
                <span>Latest upload</span>
              </li>
            </ul>
            {recentUploads.length > 0 && (
              <div className="hero-recents">
                <span>Recent uploads</span>
                <ol>
                  {recentUploads.map((file) => (
                    <li key={file.metadata_id}>
                      <button type="button" onClick={() => handleChat(file.metadata_id, file.filename)}>
                        {file.filename}
                      </button>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </aside>
        </section>

        <section className="insights-strip">
          <article>
            <h3>Workspace momentum</h3>
            <p>Keep adding papers regularly to build richer conversations with the assistant.</p>
          </article>
          <article>
            <h3>Organize with tags</h3>
            <p>Coming soon: tag PDFs to group projects, labs, or literature reviews.</p>
          </article>
          <article>
            <h3>Share conversations</h3>
            <p>Invite collaborators to view chats and continue where you left off.</p>
          </article>
        </section>

        <section className="workspace-grid">
          <article className="upload-section panel-card">
            <div className="panel-heading">
              <div>
                <h2>Upload PDF</h2>
                <p>Add new research papers to unlock AI-powered insights.</p>
              </div>
              <button
                type="button"
                className="panel-upload"
                onClick={triggerFilePicker}
                disabled={isUploading}
              >
                {isUploading ? 'Uploading…' : 'Browse files'}
              </button>
            </div>
            <div className="upload-dropzone">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                disabled={isUploading}
                id="file-upload"
                className="file-input"
              />
              <label htmlFor="file-upload" className={`file-label ${isUploading ? 'disabled' : ''}`}>
                <span className="file-label-icon">⬆️</span>
                <span className="file-label-text">
                  {isUploading ? 'Uploading your document…' : 'Drag & drop or click to select a PDF'}
                </span>
              </label>
            </div>
            {uploadError && <div className="error-message">{uploadError}</div>}
          </article>

          <article ref={librarySectionRef} className="files-section panel-card" id="my-library">
            <div className="panel-heading">
              <div>
                <h2>My library</h2>
                <p>Browse your uploaded PDFs, filtered by keywords or titles.</p>
              </div>
              {libraryFilter && (
                <button type="button" className="panel-clear" onClick={clearFilter}>
                  Clear filter
                </button>
              )}
            </div>
            {isLoading ? (
              <p className="loading-state">Loading your library…</p>
            ) : files.length === 0 ? (
              <p className="empty-state">No PDFs uploaded yet. Upload your first research paper!</p>
            ) : filteredFiles.length === 0 ? (
              <p className="empty-state">No matches found. Try a different search term.</p>
            ) : (
              <div className="files-grid">
                {filteredFiles.map((file) => (
                  <div key={file.metadata_id} className="file-card">
                    <div className="file-card-header">
                      <div className="file-badge">PDF</div>
                      <button
                        type="button"
                        className="file-delete"
                        onClick={() => handleDelete(file.metadata_id)}
                      >
                        Delete
                      </button>
                    </div>
                    <h3 title={file.filename}>{file.filename}</h3>
                    <div className="file-meta">
                      <span>{(file.size_bytes / 1024 / 1024).toFixed(2)} MB</span>
                      <span>Uploaded {new Date(file.uploaded_at).toLocaleDateString()}</span>
                    </div>
                    <div className="file-actions">
                      <button
                        onClick={() => handleChat(file.metadata_id, file.filename)}
                        className="btn-chat"
                      >
                        Open chat
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {libraryFilter && filteredFiles.length > 0 && (
              <p className="filter-note">
                Showing {filteredFiles.length} result{filteredFiles.length > 1 ? 's' : ''} for “{libraryFilter}”.
              </p>
            )}
          </article>
        </section>
      </div>
    </div>
  );
};

export default Dashboard;
