import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { papersAPI } from "../services/api";
import "./common.css";
//import "./PaperDetails.css";

const PaperDetails = ({ paperId: selectedPaperId }) => {
  const { paperId: routePaperId } = useParams();
  const paperId = selectedPaperId || routePaperId;
  const navigate = useNavigate();

  const [paper, setPaper] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchPaper();
  }, [paperId]);

  const fetchPaper = async () => {
    if (!paperId) {
      setError("Paper not found.");
      setLoading(false);
      return;
    }
    try {
      const res = await papersAPI.getPaperDetails(paperId);
      setPaper(res.data);
    } catch (err) {
      setError("Failed to load paper details");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setProcessing(true);
    setError("");

    try {
      const res = await papersAPI.analyzePaper(paperId);
      navigate(`/chat/${res.data.document_id}`);
    } catch (err) {
      setError("Failed to analyze paper");
      setProcessing(false);
    }
  };

  if (loading) {
    return <div className="loading-screen">Loading paper…</div>;
  }

  if (!paper) {
    return <div className="error-state">Paper not found.</div>;
  }

  return (
    <div className="paper-details">
      <button className="btn-back" onClick={() => navigate(-1)}>
        ← Back
      </button>

      <h1 className="paper-title">{paper.title}</h1>

      {paper.published && (
        <p className="paper-meta">
          Published: {new Date(paper.published).toLocaleDateString()}
        </p>
      )}

      <section className="paper-abstract">
        <h2>Abstract</h2>
        <p>{paper.abstract}</p>
      </section>

      <div className="paper-actions">
        <button
          className="btn-primary"
          onClick={handleAnalyze}
          disabled={processing}
        >
          {processing ? "Analyzing…" : "Analyze Paper"}
        </button>

        {paper.pdf_url && (
          <a
            href={paper.pdf_url}
            target="_blank"
            rel="noreferrer"
            className="btn-secondary"
          >
            View PDF
          </a>
        )}
      </div>

      {error && <p className="error-message">{error}</p>}
    </div>
  );
};

export default PaperDetails;
