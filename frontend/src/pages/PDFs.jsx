import { useState, useEffect } from "react";
import api from "../api/api";
import ChatModal from "../components/ChatModal";
import "./PDFs.css";
import jsPDF from "jspdf";

export default function PDFs() {
  const [file, setFile] = useState(null);
  const [uploads, setUploads] = useState([]);
  const [loading, setLoading] = useState(false);

  const [summaryOpen, setSummaryOpen] = useState(null);
  const [chatOpen, setChatOpen] = useState(null);

  useEffect(() => {
    loadUploads();
  }, []);

  const loadUploads = async () => {
    try {
      const res = await api.get("/pdf/my_uploads");
      setUploads(res.data || []);
    } catch (err) {
      console.error("Failed to load uploads", err);
    }
  };

  /* ================= UPLOAD ================= */

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a PDF file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);

    try {
      const res = await api.post("/pdf/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (res.data.status === "already_exists") {
        alert("This file is already uploaded.");
      } else if (res.data.status === "uploaded") {
        alert("Upload successful!");
      }

      setFile(null);
      loadUploads();
    } catch (err) {
      console.error("Upload failed", err);
      alert("Upload failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  /* ================= DELETE ================= */

  const handleDelete = async (documentId) => {
    if (!window.confirm("Delete this PDF?")) return;

    try {
      await api.delete(`/pdf/delete/${documentId}`);
      alert("PDF deleted successfully.");
      loadUploads();
    } catch (err) {
      console.error("Delete failed", err);
      alert("Delete failed.");
    }
  };

  return (
    <div className="pdf-page">

      <h1>Upload & Analyze PDFs</h1>

      {/* ===== UPLOAD ===== */}
      <div className="upload-box">
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files[0])}
        />

        <button onClick={handleUpload} disabled={loading}>
          {loading ? "Uploading..." : "Upload PDF"}
        </button>
      </div>

      {/* ===== LIST ===== */}
      <div className="pdf-list">
        {uploads.length === 0 ? (
          <p>No PDFs uploaded yet.</p>
        ) : (
          uploads.map((pdf) => (
            <div key={pdf._id} className="pdf-card">

              <h3 title={pdf.title}>
                {pdf.title.length > 40
                  ? pdf.title.slice(0, 40) + "..."
                  : pdf.title}
              </h3>

              <p>
                Size: {(pdf.size_bytes / 1024).toFixed(2)} KB
              </p>

              <div className="pdf-actions">

                <button
                  onClick={() => setSummaryOpen(pdf)}
                  disabled={!pdf.ready_for_chat}
                >
                  Summarize
                </button>

                <button
                  onClick={() => setChatOpen(pdf)}
                  disabled={!pdf.ready_for_chat}
                >
                  Chat with PDF
                </button>

                <button
                  className="delete-btn"
                  onClick={() => handleDelete(pdf._id)}
                >
                  Delete
                </button>

              </div>
            </div>
          ))
        )}
      </div>

      {/* ===== SUMMARY MODAL ===== */}
      {summaryOpen && (
        <SummaryModal
          documentId={summaryOpen._id}
          title={summaryOpen.title}
          onClose={() => setSummaryOpen(null)}
        />
      )}

      {/* ===== CHAT MODAL ===== */}
      {chatOpen && (
        <ChatModal
          documentId={chatOpen._id}
          paper={{ title: chatOpen.title }}
          onClose={() => setChatOpen(null)}
        />
      )}

    </div>
  );
}

/* ================= SUMMARY MODAL ================= */

function SummaryModal({ documentId, title, onClose }) {
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const res = await api.post("/pdf/summarize", {
          document_id: documentId,
        });

        setSummary(res.data.summary || "");
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
    doc.save(`${title}_summary.pdf`);
  };

  /* ================= STRUCTURED RENDER ================= */

  const renderStructuredSummary = (text) => {
    if (!text) return null;

    const sections = {};
    let currentSection = null;

    const sectionMap = {
      "objective": "Objective",
      "problem": "Problem Being Addressed",
      "methodology": "Methodology",
      "method": "Methodology",
      "key findings": "Key Findings",
      "findings": "Key Findings",
      "conclusion": "Conclusion",
      "limitations": "Limitations"
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
        sections[currentSection] = trimmed
          .replace(/^[^:]*:/, "")
          .trim();
      } else if (currentSection) {
        sections[currentSection] += "\n" + trimmed;
      }
    });

    if (Object.keys(sections).length === 0) {
      return <p style={{ whiteSpace: "pre-wrap" }}>{text}</p>;
    }

    return (
      <div className="structured-summary">
        {Object.entries(sections).map(([title, content], index) => {
          const lines = content.split("\n");

          const isBulletSection =
            title === "Key Findings" &&
            lines.some(line => line.match(/^(\d+\.|\d+\)|-)/));

          return (
            <div key={index} className="summary-section">
              <h4>{title}</h4>

              {isBulletSection ? (
                <ul>
                  {lines.map((line, i) => (
                    <li key={i}>
                      {line.replace(/^(\d+\.|\d+\)|-)\s*/, "")}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>{content.replace(/\n/g, " ")}</p>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="overlay">
      <div className="summary-modal">

        <div className="summary-header">
          <h3>Summary: {title}</h3>
          <button onClick={onClose}>✕</button>
        </div>

        <div
          className="summary-body"
          style={{ maxHeight: "65vh", overflowY: "auto" }}
        >
          {loading ? (
            <div style={{ textAlign: "center", padding: "40px" }}>
              <div className="spinner"></div>
              <p style={{ marginTop: "15px" }}>
                Generating detailed academic summary...
              </p>
              <p style={{ fontSize: "13px", opacity: 0.7 }}>
                This may take up to 2–3 minutes depending on document size.
              </p>
            </div>
          ) : (
            renderStructuredSummary(summary)
          )}
        </div>

        {!loading && (
          <button onClick={downloadPDF}>
            Download Summary as PDF
          </button>
        )}

      </div>
    </div>
  );
}