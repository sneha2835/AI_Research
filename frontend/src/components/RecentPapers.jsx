import React, { useState, useEffect } from 'react';
import { papersAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import './common.css';

const RecentPapers = ({ onSelectPaper, onProcessPaper }) => {
  const [recentPapers, setRecentPapers] = useState([]);
  const [recentlyViewed, setRecentlyViewed] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Get recent arXiv papers
      const recentResponse = await papersAPI.getRecent(5);
      setRecentPapers(recentResponse.data);

      // Get recently viewed (mixed)
      const viewedResponse = await papersAPI.getRecentlyViewed(5);
      setRecentlyViewed(viewedResponse.data);
    } catch (err) {
      console.error('Error fetching papers:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewPaper = (paper) => {
    if (onSelectPaper) {
      onSelectPaper(paper);
    }
  };

  const handleProcessPaper = async (paper) => {
    if (paper.type === 'arxiv' && onProcessPaper) {
      try {
        const response = await papersAPI.processArxiv(paper._id);
        onProcessPaper({
          ...response.data,
          paperId: paper._id,
          paperTitle: paper.title,
        });
      } catch (err) {
        alert('Failed to process paper: ' + (err.response?.data?.detail || err.message));
      }
    } else if (paper.type === 'upload') {
      // Navigate to chat for uploaded PDF
      navigate(`/chat/${paper._id}`, { 
        state: { filename: paper.title } 
      });
    }
  };

  if (loading) {
    return <div className="loading">Loading papers...</div>;
  }

  return (
    <div className="recent-papers">
      {recentlyViewed.length > 0 && (
        <div className="section">
          <h3>📚 Recently Viewed</h3>
          <div className="papers-grid">
            {recentlyViewed.map((item) => (
              <div key={item._id} className="paper-card">
                <div className="paper-header">
                  <span className={`paper-badge ${item.type}`}>
                    {item.type === 'arxiv' ? 'arXiv' : 'Upload'}
                  </span>
                  {item.source === 'arxiv' && (
                    <span className="paper-date">
                      {new Date(item.published).toLocaleDateString()}
                    </span>
                  )}
                </div>
                <h4 className="paper-title">{item.title}</h4>
                {item.abstract && (
                  <p className="paper-abstract">{item.abstract.substring(0, 150)}...</p>
                )}
                <div className="paper-actions">
                  <button
                    onClick={() => handleViewPaper(item)}
                    className="btn-outline"
                  >
                    {item.type === 'arxiv' ? 'View' : 'Open'}
                  </button>
                  <button
                    onClick={() => handleProcessPaper(item)}
                    className="btn-primary"
                  >
                    {item.type === 'arxiv' ? 'Analyze' : 'Chat'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="section">
        <h3>🔥 Recent arXiv Papers</h3>
        <div className="papers-grid">
          {recentPapers.map((paper) => (
            <div key={paper._id} className="paper-card">
              <div className="paper-header">
                <span className="paper-badge arxiv">arXiv</span>
                <span className="paper-date">
                  {new Date(paper.published).toLocaleDateString()}
                </span>
              </div>
              <h4 className="paper-title">{paper.title}</h4>
              <p className="paper-abstract">{paper.abstract.substring(0, 150)}...</p>
              <div className="paper-actions">
                <button
                  onClick={() => handleViewPaper(paper)}
                  className="btn-outline"
                >
                  View
                </button>
                <button
                  onClick={() => handleProcessPaper(paper)}
                  className="btn-primary"
                >
                  Analyze
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RecentPapers;