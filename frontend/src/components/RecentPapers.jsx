import React from "react";
import "./RecentPapers.css";

const RecentPapers = ({ papers = [], onSelect }) => {
  if (!papers.length) {
    return <p className="empty-state">No papers to display.</p>;
  }

  return (
    <div className="recent-papers-grid">
      {papers.map((item) => {
        const isArxiv = item.type === "arxiv" || item.source === "arxiv";

        const title = item.title || "Untitled paper";
        const abstract = item.abstract;
        const published = item.published;
        const paperId = item._id;
        const documentId = item.document_id;

        return (
          <div key={paperId || documentId} className="paper-card">
            <h3 className="paper-title">{title}</h3>

            {published && (
              <p className="paper-meta">
                Published: {new Date(published).toLocaleDateString()}
              </p>
            )}

            {abstract && (
              <p className="paper-abstract">
                {abstract.length > 200
                  ? abstract.slice(0, 200) + "…"
                  : abstract}
              </p>
            )}

            <div className="paper-actions">
              <button
                className="btn-primary"
                onClick={() => {
                  // arXiv → open paper details
                  if (isArxiv && paperId) {
                    onSelect(paperId);
                  }
                  // uploaded or processed → open chat
                  else if (documentId) {
                    onSelect({ document_id: documentId });
                  }
                }}
              >
                {isArxiv ? "View Paper" : "Open Chat"}
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default RecentPapers;
