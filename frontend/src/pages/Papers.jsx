import { useState, useEffect } from "react";
import api from "../api/api";
import ChatModal from "../components/ChatModal";
import "./Papers.css";
import jsPDF from "jspdf";

export default function Papers() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [selectedPaper, setSelectedPaper] = useState(null);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const res = await api.get(`/papers/search?q=${query}&limit=5`);
      setResults(res.data || []);
    } catch (err) {
      console.error("Search failed", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="papers-page">
      <h1>Search Research Papers</h1>

      <div className="search-bar">
        <input
          type="text"
          placeholder="Search by keyword..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        />
        <button onClick={handleSearch} disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      <div className="results">
        {results.length === 0 && !loading && (
          <p>No results found.</p>
        )}

        {results.map((paper) => (
          <div key={paper._id} className="paper-card">
            <h3>{paper.title}</h3>

            <p>
              {paper.abstract
                ? paper.abstract.slice(0, 220) + "..."
                : "No abstract available."}
            </p>

            <button onClick={() => setSelectedPaper(paper)}>
              View
            </button>
          </div>
        ))}
      </div>

      {selectedPaper && (
        <PaperModal
          paper={selectedPaper}
          onClose={() => setSelectedPaper(null)}
        />
      )}
    </div>
  );
}

/* ====================== PAPER MODAL ====================== */

function PaperModal({ paper, onClose }) {
  const [documentId, setDocumentId] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [summaryOpen, setSummaryOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  const ensureProcessed = async () => {
    if (documentId) return documentId;

    setProcessing(true);
    try {
      const res = await api.post(`/papers/process/${paper._id}`);
      const docId = res.data.document_id;
      setDocumentId(docId);
      return docId;
    } catch (err) {
      console.error("Processing failed", err);
      return null;
    } finally {
      setProcessing(false);
    }
  };

  const handleSummarize = async () => {
    const docId = await ensureProcessed();
    if (docId) setSummaryOpen(docId);
  };

  const handleChat = async () => {
    const docId = await ensureProcessed();
    if (docId) setChatOpen(docId);
  };

  return (
    <>
      <div className="overlay">
        <div className="overlay-content">

          <div className="overlay-header">
            <h2>{paper.title}</h2>
            <button onClick={onClose}>✕</button>
          </div>

          <p><strong>Arxiv ID:</strong> {paper.arxiv_id}</p>
          <p>
            <strong>Published:</strong>{" "}
            {new Date(paper.published).toLocaleString()}
          </p>

          <hr />

          <h3>Abstract</h3>
          <p>{paper.abstract}</p>

          <div className="modal-actions">

            {paper.pdf_url && (
              <a href={paper.pdf_url} target="_blank" rel="noreferrer">
                <button>View Paper</button>
              </a>
            )}

            <button onClick={handleSummarize} disabled={processing}>
              {processing ? "Processing..." : "Summarize Paper"}
            </button>

            <button onClick={handleChat} disabled={processing}>
              {processing ? "Processing..." : "Chat with Paper"}
            </button>

          </div>

        </div>
      </div>

      {summaryOpen && (
        <SummaryModal
          documentId={summaryOpen}
          paper={paper}
          onClose={() => setSummaryOpen(false)}
        />
      )}

      {chatOpen && (
        <ChatModal
          documentId={chatOpen}
          paper={paper}
          onClose={() => setChatOpen(false)}
        />
      )}
    </>
  );
}

/* ====================== SUMMARY MODAL ====================== */

function SummaryModal({ documentId, paper, onClose }) {
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const res = await api.post("/pdf/summarize", {
          document_id: documentId,
        });
        setSummary(res.data.summary || "No summary available.");
      } catch (err) {
        console.error("Summary failed", err);
        setSummary("Failed to generate summary.");
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [documentId]);

  const downloadPDF = () => {
    if (!summary) return;

    const doc = new jsPDF();
    const lines = doc.splitTextToSize(summary, 180);
    doc.text(lines, 10, 10);
    doc.save(`${paper.title}_summary.pdf`);
  };

  return (
    <div className="overlay">
      <div className="summary-modal upgraded">

        <div className="summary-header upgraded">
          <h2>{paper.title}</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="summary-body upgraded">
          {loading ? (
            <div className="summary-loading">
              <p>Generating professional academic summary...</p>
            </div>
          ) : (
            <StructuredSummary text={summary} />
          )}
        </div>

        {!loading && (
          <div className="summary-footer">
            <button onClick={downloadPDF}>
              Download Summary as PDF
            </button>
          </div>
        )}

      </div>
    </div>
  );
}

/* ====================== STRUCTURED SUMMARY ====================== */

function StructuredSummary({ text }) {
  if (!text) return null;

  const sections = {};
  let currentSection = null;

  const sectionMap = {
    objective: "Objective",
    problem: "Problem Being Addressed",
    methodology: "Methodology",
    method: "Methodology",
    "key findings": "Key Findings",
    findings: "Key Findings",
    conclusion: "Conclusion",
    limitations: "Limitations",
  };

  text.split("\n").forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) return;

    const lower = trimmed.toLowerCase();

    const matchedSection = Object.keys(sectionMap).find(key =>
      lower.startsWith(key)
    );

    if (matchedSection) {
      currentSection = sectionMap[matchedSection];
      sections[currentSection] = trimmed.replace(/^[^:]*:/, "").trim();
    } else if (currentSection) {
      sections[currentSection] += " " + trimmed;
    }
  });

  if (Object.keys(sections).length === 0) {
    return <p style={{ whiteSpace: "pre-wrap" }}>{text}</p>;
  }

  return (
    <div className="structured-summary">
      {Object.entries(sections).map(([title, content], index) => (
        <div key={index} className="summary-section">
          <h4>{title}</h4>
          <p>{content}</p>
        </div>
      ))}
    </div>
  );
}