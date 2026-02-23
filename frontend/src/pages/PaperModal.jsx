import { useState } from "react";
import api from "../api/api";
import "./PaperModal.css";

export default function PaperModal({ paper, onClose }) {
  const [mode, setMode] = useState("view");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState([]);
  const [asking, setAsking] = useState(false);

  /* ================= SUMMARIZE ================= */

  const handleSummarize = async () => {
    setMode("summary");
    setLoading(true);

    try {
      const res = await api.post(`/papers/analyze/${paper.id}`);
      setSummary(res.data?.summary || JSON.stringify(res.data));
    } catch (err) {
      console.error("Summary failed", err);
      setSummary("Failed to generate summary.");
    } finally {
      setLoading(false);
    }
  };

  /* ================= Q & A ================= */

  const handleAsk = async () => {
    if (!question.trim() || asking) return;

    const userQuestion = question.trim();

    setChat((prev) => [...prev, { role: "user", content: userQuestion }]);
    setQuestion("");
    setAsking(true);

    try {
      const res = await api.post(`/papers/process/${paper.id}`, {
        question: userQuestion,
      });

      const answer =
        res.data?.answer ||
        res.data?.response ||
        JSON.stringify(res.data);

      setChat((prev) => [
        ...prev,
        { role: "assistant", content: answer },
      ]);
    } catch (err) {
      console.error("Question failed", err);
      setChat((prev) => [
        ...prev,
        { role: "assistant", content: "Error processing question." },
      ]);
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="overlay">
      <div className="overlay-content">

        <div className="overlay-header">
          <h2>{paper.title}</h2>
          <button onClick={onClose}>✕</button>
        </div>

        {/* ===== VIEW MODE ===== */}
        {mode === "view" && (
          <>
            <p><strong>Authors:</strong> {paper.authors?.join(", ")}</p>
            <p><strong>Published:</strong> {paper.published}</p>
            <p>{paper.summary}</p>

            <div className="modal-actions">
              <a
                href={`https://arxiv.org/pdf/${paper.id}.pdf`}
                target="_blank"
                rel="noreferrer"
              >
                <button>View Full Paper</button>
              </a>

              <button onClick={handleSummarize}>
                Summarize
              </button>

              <button onClick={() => setMode("chat")}>
                Q & A
              </button>
            </div>
          </>
        )}

        {/* ===== SUMMARY MODE ===== */}
        {mode === "summary" && (
          <>
            {loading ? (
              <p>Generating summary...</p>
            ) : (
              <div className="analysis-box">
                {summary}
              </div>
            )}

            <button onClick={() => setMode("view")}>
              Back
            </button>
          </>
        )}

        {/* ===== CHAT MODE ===== */}
        {mode === "chat" && (
          <>
            <div className="chat-box">
              {chat.map((msg, index) => (
                <div
                  key={index}
                  className={`chat-message ${msg.role}`}
                >
                  {msg.content}
                </div>
              ))}
            </div>

            <div className="chat-input">
              <input
                type="text"
                placeholder="Ask a question..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={asking}
              />
              <button onClick={handleAsk} disabled={asking}>
                {asking ? "Thinking..." : "Ask"}
              </button>
            </div>

            <button onClick={() => setMode("view")}>
              Back
            </button>
          </>
        )}

      </div>
    </div>
  );
}