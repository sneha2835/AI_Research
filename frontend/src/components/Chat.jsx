import React, { useEffect, useRef, useState } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import { pdfAPI } from "../services/api";

import "./common.css";
import "./Chat.css";

const Chat = () => {
  const { document_id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const title = location.state?.title || "Document";

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef(null);

  // ==================================================
  // 🔄 Load chat history
  // ==================================================
  useEffect(() => {
    if (!document_id) return;
    loadHistory();
  }, [document_id]);

  const loadHistory = async () => {
    try {
      const res = await pdfAPI.getChatHistory(document_id);
      setMessages(res.data.messages || []);
    } catch (err) {
      console.error("Failed to load chat history", err);
    }
  };

  // ==================================================
  // ⬇️ Auto-scroll
  // ==================================================
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ==================================================
  // ❓ Ask question
  // ==================================================
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = {
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await pdfAPI.ask(document_id, input);

      const assistantMessage = {
        role: "assistant",
        content: res.data.answer,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, something went wrong. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // ==================================================
  // 🧱 UI
  // ==================================================
  return (
    <div className="chat-container">
      <div className="chat-header">
        <button onClick={() => navigate("/dashboard")} className="back-button">
          ← Back
        </button>
        <div className="chat-title">
          <h2>📄 {title}</h2>
          <p>Ask questions about this document</p>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-content">{msg.content}</div>
          </div>
        ))}

        {isLoading && (
          <div className="message assistant">
            <div className="message-content">Thinking…</div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="chat-input-form">
        <input
          type="text"
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question…"
          disabled={isLoading}
        />
        <button
          type="submit"
          className="btn-send"
          disabled={isLoading || !input.trim()}
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default Chat;
