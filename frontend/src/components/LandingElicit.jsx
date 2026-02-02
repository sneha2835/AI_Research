import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './LandingElicit.css';

const LandingElicit = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [recentSearches] = useState([
    { id: 1, query: 'langgraph framework', tool: 'Find papers', time: '2:11pm Dec 26' },
    { id: 2, query: 'LLM agent architecture', tool: 'Find papers', time: '10:45am Dec 25' },
    { id: 3, query: 'retrieval augmented generation', tool: 'Paper chat', time: '9:22am Dec 24' }
  ]);

  const handleSearch = () => {
    if (searchQuery.trim()) {
      navigate(`/dashboard?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="elicit-landing">
      {/* Top Navigation */}
      <nav className="elicit-nav">
        <div className="nav-left">
          <div className="elicit-logo">🧠 Research Companion</div>
          <div className="elicit-nav-links">
            <a href="#" className="nav-link">Recents</a>
            <a href="#" className="nav-link">Library</a>
            <a href="#" className="nav-link">Alerts</a>
          </div>
        </div>
        <div className="nav-right">
          <button className="btn-upgrade">⭐ Upgrade</button>
          <div className="help-menu">
            Help <span className="dropdown-arrow">▾</span>
          </div>
          <div className="user-profile" onClick={() => navigate('/login')}>
            <span>Sign In</span>
          </div>
        </div>
      </nav>

      <div className="elicit-content">
        {/* Left Sidebar */}
        <aside className="elicit-sidebar">
          <div className="sidebar-section">
            <div className="sidebar-section-title">Tools</div>
            <div className="sidebar-item active" onClick={() => navigate('/dashboard')}>
              <span className="sidebar-item-icon">🔍</span>
              <span>Find papers</span>
            </div>
            <div className="sidebar-item" onClick={() => navigate('/dashboard')}>
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
              Agents <span className="beta-badge">BETA</span>
            </div>
            <div className="sidebar-item">
              <span className="sidebar-item-icon">🎯</span>
              <span>Competitive landscape</span>
              <span className="pro-badge">PRO</span>
            </div>
            <div className="sidebar-item">
              <span className="sidebar-item-icon">🤖</span>
              <span>General research agent</span>
              <span className="pro-badge">PRO</span>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="elicit-main">
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
                    <option>Books</option>
                    <option>Preprints</option>
                  </select>
                </div>
                <button className="btn-search" onClick={handleSearch}>
                  → Search
                </button>
              </div>
            </div>
          </div>

          {/* Recents Section */}
          <div className="elicit-recents">
            <div className="recents-header">
              <div className="recents-title">Recents</div>
              <a href="#" className="view-all-link">View all</a>
            </div>
            <div className="recents-list">
              {recentSearches.map((item) => (
                <div key={item.id} className="recent-item" onClick={() => setSearchQuery(item.query)}>
                  <div className="recent-item-left">
                    <span className="recent-icon">🔍</span>
                    <span className="recent-query">{item.query}</span>
                  </div>
                  <div className="recent-item-right">
                    <span className="recent-tool">{item.tool}</span>
                    <span className="recent-time">{item.time}</span>
                    <span className="recent-more">⋯</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default LandingElicit;
