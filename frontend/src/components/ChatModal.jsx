import { useState, useEffect, useRef } from "react";
import api from "../api/api";
import { useAuth } from "../auth/AuthContext";
import "../pages/Papers.css";

export default function ChatModal({ documentId, paper, onClose }) {
  const { user } = useAuth();

  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  /* ================= SAVE LAST SESSION ================= */

  useEffect(() => {
    if (documentId) {
      localStorage.setItem("last_chat_document_id", documentId);
      localStorage.setItem("last_chat_paper_title", paper?.title || "");
    }
  }, [documentId, paper?.title]);

  /* ================= LOAD HISTORY ================= */

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await api.get(`/chat/${documentId}`);

        const qaMessages = res.data?.messages?.filter(
          (msg) => msg.type === "qa"
        );

        if (qaMessages?.length) {
          setMessages(qaMessages);
        } else {
          injectGreeting();
        }
      } catch (err) {
        if (err.response?.status === 409) {
          setMessages([
            {
              role: "assistant",
              type: "qa",
              content:
                "This document is still being processed. Please wait a moment and try again."
            }
          ]);
        } else {
          injectGreeting();
        }
      }
    };

    const injectGreeting = () => {
      setMessages([
        {
          role: "assistant",
          type: "qa",
          content: `Hello ${
            user?.name || user?.email || "User"
          }, how may I assist you today?`
        }
      ]);
    };

    if (documentId) fetchHistory();
  }, [documentId, user]);

  /* ================= AUTO SCROLL ================= */

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  /* ================= SEND MESSAGE ================= */

  const handleSend = async (manualQuery = null) => {
    const trimmed = (manualQuery || query).trim();
    if (!trimmed || loading) return;

    const userMessage = {
      role: "user",
      type: "qa",
      content: trimmed
    };

    setMessages((prev) => [...prev, userMessage]);
    setQuery("");
    setLoading(true);

    try {
      const res = await api.post("/pdf/ask", {
        document_id: documentId,
        query: trimmed,
        n_results: 5
      });

      const assistantMessage = {
        role: "assistant",
        type: "qa",
        content: res.data?.answer || "No response received.",
        followups: res.data?.followups || [],
        needsWeb: res.data?.needs_web_search || false
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      let errorMessage =
        "Something went wrong while processing your question.";

      if (err.response?.status === 409) {
        errorMessage =
          "This document is still being processed. Please try again shortly.";
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          type: "qa",
          content: errorMessage
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleFollowupClick = (text) => {
    handleSend(text);
  };

  return (
    <div className="overlay">
      <div className="chat-modal">

        {/* ================= HEADER ================= */}

        <div className="chat-header">
          <h3>Chat with {paper?.title}</h3>
          <button onClick={onClose}>✕</button>
        </div>

        {/* ================= BODY ================= */}

        <div className="chat-body">
          {messages.map((msg, i) => (
            <div key={i}>
              <div
                className={`chat-bubble ${msg.role}`}
                style={{ whiteSpace: "pre-wrap" }}
              >
                {msg.content}
              </div>

              {msg.needsWeb && (
                <div className="web-indicator">
                  🌐 This may require external search.
                </div>
              )}

              {msg.followups?.length > 0 && (
                <div className="followups">
                  {msg.followups.map((f, index) => (
                    <button
                      key={index}
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

          {loading && (
            <div className="chat-bubble assistant thinking">
              Thinking...
            </div>
          )}

          <div ref={bottomRef}></div>
        </div>

        {/* ================= FOOTER ================= */}

        <div className="chat-footer">
          <input
            type="text"
            placeholder="Ask a research question..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            disabled={loading}
          />

          <button onClick={() => handleSend()} disabled={loading}>
            {loading ? "Thinking..." : "Send"}
          </button>
        </div>

      </div>
    </div>
  );
}