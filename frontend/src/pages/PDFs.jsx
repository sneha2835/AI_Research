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

        setSummary(res.data.summary || res.data || "");
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
    if (!summary) {
      alert("No summary available to download.");
      return;
    }

    const doc = new jsPDF();
    const lines = doc.splitTextToSize(summary, 180);

    doc.text(lines, 10, 10);
    doc.save(`${title}_summary.pdf`);
  };

  return (
    <div className="overlay">
      <div className="summary-modal">

        <div className="summary-header">
          <h3>Summary: {title}</h3>
          <button onClick={onClose}>✕</button>
        </div>

        <div className="summary-body">
          {loading ? "Generating summary..." : summary}
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