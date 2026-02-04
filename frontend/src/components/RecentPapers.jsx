import React from 'react';
//import './RecentPapers.css';

const RecentPapers = ({ papers = [], onSelect }) => {
  if (!papers.length) {
    return <p className="empty-state">No papers to show.</p>;
  }

  return (
    <div className="recent-papers-grid">
      {papers.map((paper) => (
        <div
          key={paper._id || paper.document_id}
          className="paper-card"
          onClick={() => onSelect(paper)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter') onSelect(paper);
          }}
        >
          <h3 className="paper-title">
            {paper.title || 'Untitled paper'}
          </h3>

          {paper.abstract && (
            <p className="paper-abstract">
              {paper.abstract.slice(0, 180)}…
            </p>
          )}

          {paper.published && (
            <span className="paper-meta">
              Published: {new Date(paper.published).toLocaleDateString()}
            </span>
          )}

          {paper.type && (
            <span className={`paper-badge ${paper.type}`}>
              {paper.type === 'arxiv' ? 'arXiv' : 'PDF'}
            </span>
          )}
        </div>
      ))}
    </div>
  );
};

export default RecentPapers;
