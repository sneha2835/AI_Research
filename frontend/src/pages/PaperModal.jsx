import { useState, useRef, useEffect } from "react";
import api from "../api/api";
import "./PaperModal.css";

export default function PaperModal({ paper, onClose }) {
  const [mode, setMode] = useState("view");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);

  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState([]);
  const [asking, setAsking] = useState(false);

  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat]);

  /* ================= FORMAT SUMMARY ================= */

  const formatSummary = (text) => {
    if (!text) return null;

    return text.split("\n").map((line, index) => {
      const isSection =
        line.startsWith("Objective:") ||
        line.startsWith("Problem Being Addressed:") ||
        line.startsWith("Methodology:") ||
        line.startsWith("Key Findings:") ||
        line.startsWith("Conclusion:") ||
        line.startsWith("Limitations:");

      return (
        <p
          key={index}
          style={{
            fontWeight: isSection ? "600" : "400",
            marginBottom: "10px",
            lineHeight: "1.6",
          }}
        >
          {line}
        </p>
      );
    });
  };

  /* ================= SUMMARIZE ================= */

  const handleSummarize = async () => {
    setMode("summary");
    setLoading(true);
    setSummary("");

    try {
      const res = await api.post(`/papers/analyze/${paper.id}`);
      setSummary(res.data?.summary || "No summary returned.");
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
        "No response received.";

      const followups = res.data?.followups || [];

      setChat((prev) => [
        ...prev,
        { role: "assistant", content: answer, followups },
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

  /* ================= CLICK FOLLOWUP ================= */

  const handleFollowupClick = (text) => {
    setQuestion(text);
  };

  return (
    <div className="overlay">
      <div className="overlay-content">

        <div className="overlay-header">
          <h2>{paper.title}</h2>
          <button onClick={onClose}>✕</button>
        </div>

        {/* ================= VIEW MODE ================= */}
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

        {/* ================= SUMMARY MODE ================= */}
        {mode === "summary" && (
          <>
            {loading ? (
              <div style={{ textAlign: "center", padding: "30px" }}>
                <div className="spinner"></div>
                <p style={{ marginTop: "15px" }}>
                  Generating detailed academic summary...
                </p>
                <p style={{ fontSize: "13px", opacity: 0.7 }}>
                  This may take up to 2–3 minutes.
                </p>
              </div>
            ) : (
              <div
                className="analysis-box"
                style={{ maxHeight: "60vh", overflowY: "auto" }}
              >
              {renderStructuredSummary(summary)}              
              </div>
            )}

            <button onClick={() => setMode("view")}>
              Back
            </button>
          </>
        )}

        {/* ================= CHAT MODE ================= */}
        {mode === "chat" && (
          <>
            <div className="chat-box">
              {chat.map((msg, index) => (
                <div key={index}>
                  <div className={`chat-message ${msg.role}`}>
                    {msg.content}
                  </div>

                  {/* FOLLOWUPS */}
                  {msg.followups && msg.followups.length > 0 && (
                    <div className="followups">
                      {msg.followups.map((f, i) => (
                        <button
                          key={i}
                          className="followup-btn"
                          onClick={() => handleFollowupClick(f)}
                        >
                          {f}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}

              {asking && (
                <div className="chat-message assistant thinking">
                  Thinking...
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            <div className="chat-input">
              <input
                type="text"
                placeholder="Ask a research question..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={asking}
              />
              <button onClick={handleAsk} disabled={asking}>
                Ask
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