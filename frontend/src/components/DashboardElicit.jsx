import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { pdfAPI, papersAPI } from '../services/api';
import './DashboardElicit.css';

const DashboardElicit = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const fileInputRef = useRef(null);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [papers, setPapers] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [sortBy, setSortBy] = useState('relevance');
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [activeTab, setActiveTab] = useState('papers'); // 'papers' or 'library'
  const [showFullTextBanner, setShowFullTextBanner] = useState(true);
  const [deleteConfirm, setDeleteConfirm] = useState(null); // {id, filename}
  const [isSummarizing, setIsSummarizing] = useState(null); // file id being summarized
  const [summaryModal, setSummaryModal] = useState(null); // {filename, summary}
  const [recentlyViewed, setRecentlyViewed] = useState([]);
  
  useEffect(() => {
    // Get search query from URL params
    const params = new URLSearchParams(location.search);
    const query = params.get('search');
    if (query) {
      setSearchQuery(query);
      setActiveTab('papers');
      handleSearch(query);
      fetchRecentlyViewed();
    } else {
      // Load user's library by default
      setActiveTab('library');
      fetchUploadedFiles();
    }
  }, [location.search]);

  const fetchUploadedFiles = async () => {
    try {
      const response = await pdfAPI.getMyUploads();
      setUploadedFiles(response.data.files || []);
    } catch (error) {
      console.error('Failed to fetch files:', error);
    }
  };

  const fetchRecentlyViewed = async () => {
    try {
      const response = await papersAPI.getRecentlyViewed(5);
      setRecentlyViewed(response.data || []);
    } catch (error) {
      console.error('Failed to fetch recently viewed:', error);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Only PDF files are supported');
      return;
    }

    setIsUploading(true);
    try {
      await pdfAPI.upload(file);
      await fetchUploadedFiles();
      e.target.value = '';
      alert('PDF uploaded successfully!');
    } catch (error) {
      alert('Upload failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsUploading(false);
    }
  };

  const handleLibraryFileClick = (file) => {
    navigate(`/chat/${file.metadata_id}`, {
      state: { filename: file.filename }
    });
  };

  const handleSummarize = async (e, file) => {
    e.stopPropagation();
    setIsSummarizing(file.metadata_id);
    try {
      const response = await pdfAPI.summarize({ document_id: file.metadata_id });
      setSummaryModal({ filename: file.filename, summary: response.data.summary });
    } catch (error) {
      alert('Failed to generate summary: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsSummarizing(null);
    }
  };

  const handleDeleteClick = (e, file) => {
    e.stopPropagation();
    setDeleteConfirm({ id: file.metadata_id, filename: file.filename });
  };

  const confirmDelete = async () => {
    if (!deleteConfirm) return;
    try {
      await pdfAPI.deletePDF(deleteConfirm.id);
      await fetchUploadedFiles();
      setDeleteConfirm(null);
    } catch (error) {
      alert('Failed to delete: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleSearch = async (query = searchQuery) => {
    if (!query.trim()) return;
    
    setIsSearching(true);
    setActiveTab('papers');
    try {
      const response = await papersAPI.search(query, 20);
      // Backend returns array directly, map arxiv_id to id
      const papersData = response.data || [];
      const normalizedPapers = papersData.map(paper => ({
        ...paper,
        id: paper.arxiv_id || paper._id,
        summary: paper.abstract || paper.summary
      }));
      setPapers(normalizedPapers);
    } catch (error) {
      console.error('Search failed:', error);
      alert('Search failed: ' + (error.response?.data?.detail || error.message));
      setPapers([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handlePaperClick = async (paper) => {
    setSelectedPaper(paper);
    
    // Process the paper
    try {
      const response = await papersAPI.analyze(paper.id);
      if (response.data.metadata_id) {
        navigate(`/chat/${response.data.metadata_id}`, {
          state: { filename: response.data.filename || paper.title }
        });
      }
    } catch (error) {
      console.error('Failed to process paper:', error);
      alert('Failed to process paper: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="dashboard-elicit">
      {/* Top Navigation - matching landing page */}
      <nav className="elicit-nav">
        <div className="nav-left">
          <div className="elicit-logo" onClick={() => navigate('/')}>🧠 Research Companion</div>
          <div className="elicit-nav-links">
            <a href="#" className="nav-link">Recents</a>
            <a 
              href="#" 
              className={`nav-link ${activeTab === 'library' ? 'active' : ''}`}
              onClick={(e) => {
                e.preventDefault();
                setActiveTab('library');
                fetchUploadedFiles();
              }}
            >
              Library
            </a>
            <a href="#" className="nav-link">Alerts</a>
          </div>
        </div>
        <div className="nav-right">
          <button className="btn-upgrade">⭐ Upgrade</button>
          <div className="help-menu">Help ▾</div>
          <div className="user-profile" onClick={() => navigate('/profile')}>
            {user?.email || 'User'}
          </div>
        </div>
      </nav>

      <div className="elicit-content">
        {/* Left Sidebar - matching landing page */}
        <aside className="elicit-sidebar">
          <div className="sidebar-section">
            <div className="sidebar-section-title">Tools</div>
            <div className={`sidebar-item ${activeTab === 'papers' ? 'active' : ''}`} onClick={() => setActiveTab('papers')}>
              <span className="sidebar-item-icon">🔍</span>
              <span>Find papers</span>
            </div>
            <div className={`sidebar-item ${activeTab === 'library' ? 'active' : ''}`} onClick={() => { setActiveTab('library'); fetchUploadedFiles(); }}>
              <span className="sidebar-item-icon">💬</span>
              <span>Paper chat</span>
            </div>
            <div className="sidebar-item">
              <span className="sidebar-item-icon">📊</span>
              <span>Extract data</span>
              <span className="pro-badge">PRO</span>
            </div>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-section-title">Popular workflows</div>
            <div className="sidebar-item">
              <span className="sidebar-item-icon">📄</span>
              <span>Research report</span>
            </div>
            <div className="sidebar-item">
              <span className="sidebar-item-icon">📚</span>
              <span>Systematic review</span>
              <span className="pro-badge">PRO</span>
            </div>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-section-title">
              My Library <span className="sidebar-count">{uploadedFiles.length}</span>
            </div>
            <div className="sidebar-item" onClick={() => fileInputRef.current?.click()}>
              <span className="sidebar-item-icon">📤</span>
              <span>Upload PDF</span>
            </div>
            <div className="sidebar-item" onClick={logout}>
              <span className="sidebar-item-icon">🚪</span>
              <span>Logout</span>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="elicit-main">
          {/* Search Box */}
          <div className="elicit-hero">
            <div className="hero-search-container">
              <input
                type="text"
                className="hero-search-input"
                placeholder="Ask a research question to search and explore academic literature"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={handleKeyPress}
              />
              <div className="hero-search-footer">
                <div className="source-selector">
                  <label className="source-label">Source</label>
                  <select className="source-dropdown">
                    <option>Research papers</option>
                  </select>
                </div>
                <button className="btn-search" onClick={() => handleSearch()}>
                  → Search
                </button>
              </div>
            </div>
          </div>

          {/* Hidden file input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            style={{ display: 'none' }}
            onChange={handleFileUpload}
          />
          {/* Content Area */}
          <div className="elicit-results">
            {activeTab === 'library' ? (
              /* Library View */
              <div className="library-view">
                <div className="library-header">
                  <h2>Your PDF Library</h2>
                  <p className="library-count">{uploadedFiles.length} documents</p>
                </div>
                
                {uploadedFiles.length === 0 ? (
                  <div className="empty-state">
                    <div className="empty-icon">📚</div>
                    <h3>No PDFs uploaded yet</h3>
                    <p>Upload your first research paper to get started</p>
                    <button 
                      className="btn-upload-primary"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      📤 Upload PDF
                    </button>
                  </div>
                ) : (
                  <div className="library-grid">
                    {uploadedFiles.map((file) => (
                      <div 
                        key={file.metadata_id} 
                        className="library-card"
                      >
                        <div className="card-icon">📄</div>
                        <h3 className="card-title">{file.filename}</h3>
                        <div className="card-meta">
                          <span>{Math.round(file.size_bytes / 1024)} KB</span>
                          <span>•</span>
                          <span>{new Date(file.uploaded_at).toLocaleDateString()}</span>
                        </div>
                        <div className="card-actions">
                          <button 
                            className="btn-action-small btn-summarize"
                            onClick={(e) => handleSummarize(e, file)}
                            disabled={isSummarizing === file.metadata_id}
                          >
                            {isSummarizing === file.metadata_id ? '⏳' : '📝'} Summarize
                          </button>
                          <button 
                            className="btn-action-small btn-chat"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleLibraryFileClick(file);
                            }}
                          >
                            💬 Chat
                          </button>
                          <button 
                            className="btn-action-small btn-delete"
                            onClick={(e) => handleDeleteClick(e, file)}
                          >
                            🗑️ Delete
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : isSearching ? (
              <div className="loading-state">
                <div className="spinner"></div>
                <p>Searching for papers...</p>
              </div>
            ) : papers.length > 0 ? (
              /* Search Results */
              <div className="search-results">
                <div className="results-header-simple">
                  <h3>{papers.length} papers found</h3>
                </div>
                <div className="results-list-simple">
                  {papers.map((paper, index) => (
                    <div
                      key={paper.id || index}
                      className="result-card"
                      onClick={() => handlePaperClick(paper)}
                    >
                      <h3 className="paper-title">{paper.title}</h3>
                      <div className="paper-authors">
                        {paper.authors?.join(', ') || 'arXiv'}
                      </div>
                      <p className="paper-abstract">
                        {paper.summary?.substring(0, 250)}...
                      </p>
                      <div className="paper-footer">
                        <span className="paper-date">
                          {paper.published?.split('T')[0] || 'N/A'}
                        </span>
                        {paper.pdf_url && (
                          <a
                            href={paper.pdf_url}
                            className="paper-pdf-link"
                            onClick={(e) => e.stopPropagation()}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            📄 View PDF
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">🔍</div>
                <h3>Start your research</h3>
                <p>Enter a research question above to find relevant papers</p>
              </div>
            )}

            {/* Recently Viewed Section - shows when in papers tab */}
            {activeTab === 'papers' && recentlyViewed.length > 0 && (
              <div className="recently-viewed-section">
                <h3 className="section-title">📚 Recently Viewed Papers</h3>
                <div className="recent-papers-list">
                  {recentlyViewed.map((paper) => (
                    <div key={paper._id} className="recent-paper-card" onClick={() => handlePaperClick(paper)}>
                      <div className="recent-paper-badge">{paper.source || 'arXiv'}</div>
                      <h4 className="recent-paper-title">{paper.title}</h4>
                      <p className="recent-paper-meta">
                        {new Date(paper.published || paper.viewed_at).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="modal-overlay" onClick={() => setDeleteConfirm(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Delete PDF</h3>
            <p>Are you sure you want to delete <strong>{deleteConfirm.filename}</strong>?</p>
            <p className="warning-text">This will also delete all chat history associated with this document.</p>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setDeleteConfirm(null)}>Cancel</button>
              <button className="btn-delete-confirm" onClick={confirmDelete}>Delete</button>
            </div>
          </div>
        </div>
      )}

      {/* Summary Modal */}
      {summaryModal && (
        <div className="modal-overlay" onClick={() => setSummaryModal(null)}>
          <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
            <h3>📄 Summary: {summaryModal.filename}</h3>
            <div className="summary-content">
              {summaryModal.summary}
            </div>
            <div className="modal-actions">
              <button className="btn-primary" onClick={() => setSummaryModal(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardElicit;
