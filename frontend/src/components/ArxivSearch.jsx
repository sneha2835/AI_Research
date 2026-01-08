import React, { useState } from 'react';
import { papersAPI } from '../services/api';
import './common.css';

const ArxivSearch = ({ onSelectPaper, onProcessPaper }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError('');

    try {
      const response = await papersAPI.search(query);
      setResults(response.data);
    } catch (err) {
      setError('Search failed. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleProcessPaper = async (paperId, paperTitle) => {
    if (!onProcessPaper) return;
    
    try {
      const response = await papersAPI.processArxiv(paperId);
      onProcessPaper({
        ...response.data,
        paperId,
        paperTitle,
      });
    } catch (err) {
      alert('Failed to process paper: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="arxiv-search">
      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search arXiv papers (AI, ML, CV, NLP...)"
          className="search-input"
        />
        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <div className="error-message">{error}</div>}

      {results.length > 0 && (
        <div className="results-container">
          <h3>Search Results ({results.length})</h3>
          <div className="results-list">
            {results.map((paper) => (
              <div key={paper._id} className="paper-card">
                <div className="paper-header">
                  <span className="paper-badge">arXiv</span>
                  <span className="paper-date">
                    {new Date(paper.published).toLocaleDateString()}
                  </span>
                </div>
                <h4 className="paper-title">{paper.title}</h4>
                <p className="paper-abstract">{paper.abstract.substring(0, 200)}...</p>
                <div className="paper-actions">
                  <button
                    onClick={() => onSelectPaper && onSelectPaper(paper)}
                    className="btn-outline"
                  >
                    View Details
                  </button>
                  <button
                    onClick={() => handleProcessPaper(paper._id, paper.title)}
                    className="btn-primary"
                  >
                    Analyze Paper
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ArxivSearch;