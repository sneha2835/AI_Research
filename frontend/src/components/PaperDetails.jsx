import React, { useState, useEffect } from 'react';
import { papersAPI } from '../services/api';
import './common.css';

const PaperDetail = ({ paperId, onBack, onProcess }) => {
  const [paper, setPaper] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    fetchPaperDetails();
  }, [paperId]);

  const fetchPaperDetails = async () => {
    setLoading(true);
    try {
      const response = await papersAPI.getPaperDetails(paperId);
      setPaper(response.data);
      // Track view
      await papersAPI.trackView(paperId);
    } catch (err) {
      setError('Failed to load paper details');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleProcess = async () => {
    if (!onProcess) return;
    
    setProcessing(true);
    try {
      const response = await papersAPI.processArxiv(paperId);
      onProcess({
        ...response.data,
        paperId,
        paperTitle: paper.title,
      });
    } catch (err) {
      alert('Failed to process paper: ' + (err.response?.data?.detail || err.message));
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading paper details...</div>;
  }

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  if (!paper) {
    return <div className="error-message">Paper not found</div>;
  }

  return (
    <div className="paper-detail">
      <div className="paper-detail-header">
        <button onClick={onBack} className="back-button">
          ← Back
        </button>
        <h2>Paper Details</h2>
      </div>

      <div className="paper-content">
        <div className="paper-meta">
          <span className="paper-source">arXiv</span>
          <span className="paper-date">
            Published: {new Date(paper.published).toLocaleDateString()}
          </span>
          {paper.categories && (
            <span className="paper-categories">
              Categories: {paper.categories.join(', ')}
            </span>
          )}
        </div>

        <h1 className="paper-title">{paper.title}</h1>
        
        <div className="paper-abstract">
          <h3>Abstract</h3>
          <p>{paper.abstract}</p>
        </div>

        <div className="paper-links">
          <a 
            href={paper.pdf_url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="btn-outline"
          >
            📄 View PDF on arXiv
          </a>
        </div>

        <div className="paper-actions">
          <button
            onClick={handleProcess}
            disabled={processing}
            className="btn-primary btn-large"
          >
            {processing ? 'Processing...' : '📊 Analyze this Paper'}
          </button>
          <p className="action-hint">
            This will download the PDF, extract text, and make it available for Q&A
          </p>
        </div>
      </div>
    </div>
  );
};

export default PaperDetail;