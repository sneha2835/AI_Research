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

        if (qaMessages && qaMessages.length > 0) {
          setMessages(qaMessages);
        } else {
          injectGreeting();
        }

      } catch (err) {
        console.error("Chat history failed", err);
        injectGreeting();
      }
    };

    const injectGreeting = () => {
      setMessages([
        {
          role: "assistant",
          type: "qa",
          content: `Hello ${user?.name || user?.email || "User"}, how may I assist you today?`
        }
      ]);
    };

    if (documentId) fetchHistory();
  }, [documentId, user]);

  /* ================= AUTO SCROLL ================= */

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  /* ================= SEND MESSAGE ================= */

  const handleSend = async () => {
    const trimmed = query.trim();
    if (!trimmed || loading) return;

    const userMessage = { role: "user", type: "qa", content: trimmed };
    setMessages(prev => [...prev, userMessage]);
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
        content: res.data?.answer || "No response received."
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (err) {
      console.error("Chat failed", err);

      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          type: "qa",
          content: "Something went wrong while processing your question."
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="overlay">
      <div className="chat-modal">

        <div className="chat-header">
          <h3>Chat with {paper?.title}</h3>
          <button onClick={onClose}>✕</button>
        </div>

        <div className="chat-body">
          {messages.map((msg, i) => (
            <div key={i} className={`chat-bubble ${msg.role}`}>
              {msg.content}
            </div>
          ))}
          <div ref={bottomRef}></div>
        </div>

        <div className="chat-footer">
          <input
            type="text"
            placeholder="Ask a question..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            disabled={loading}
          />
          <button onClick={handleSend} disabled={loading}>
            {loading ? "Thinking..." : "Send"}
          </button>
        </div>

      </div>
    </div>
  );
}