import React, { useState, useEffect, useRef } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { pdfAPI } from '../services/api';
import './common.css';
import './Chat.css';
import './ChatExtensions.css';

const Chat = () => {
  const { metadataId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const filename = location.state?.filename || 'Document';
  
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isExtracted, setIsExtracted] = useState(false);
  const [summary, setSummary] = useState('');
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [clearConfirm, setClearConfirm] = useState(false);
  const messagesEndRef = useRef(null);
  const hasExtractedRef = useRef(false);

  useEffect(() => {
    loadChatHistory();
  }, [metadataId]);

  useEffect(() => {
    if (!hasExtractedRef.current) {
      extractChunks();
    }
  }, [metadataId, messages.length]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChatHistory = async () => {
    if (!metadataId) return;
    
    try {
      const response = await pdfAPI.getChatHistory(metadataId);
      if (response.data.messages && response.data.messages.length > 0) {
        // Restore previous conversation
        const loadedMessages = response.data.messages.map(msg => ({
          role: msg.role,
          content: msg.content
        }));
        setMessages(loadedMessages);
        setIsExtracted(true); // If there's history, PDF was already processed
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
      // Continue without history
    }
  };

  const extractChunks = async () => {
    if (!metadataId) return;
    
    // Skip if already extracted (history loaded or messages exist)
    if (isExtracted || messages.length > 0 || hasExtractedRef.current) return;
    
    hasExtractedRef.current = true;
    setIsExtracting(true);
    try {
      await pdfAPI.extractChunks(metadataId);
      setIsExtracted(true);
      
      const welcomeMessage = {
        role: 'assistant',
        content: `PDF "${filename}" has been processed and is ready for questions! You can now ask me anything about this document.`
      };
      
      setMessages([welcomeMessage]);
      
      // Save welcome message to database
      await pdfAPI.saveChatMessage(metadataId, 'assistant', welcomeMessage.content);
    } catch (error) {
      console.error('Failed to extract chunks:', error);
      hasExtractedRef.current = false;
      const errorMessage = {
        role: 'assistant',
        content: 'Failed to process the PDF. Please try again later.'
      };
      setMessages([errorMessage]);
    } finally {
      setIsExtracting(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading || !isExtracted) return;

    const userMessage = { role: 'user', content: inputValue };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInputValue('');
    setIsLoading(true);

    try {
      // Save user message to database
      await pdfAPI.saveChatMessage(metadataId, 'user', userMessage.content);
      
      // Build conversation history for context
      const conversationHistory = updatedMessages
        .slice(-6) // Last 3 exchanges (6 messages)
        .map(msg => `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`)
        .join('\n\n');

      const response = await pdfAPI.askWithHistory(inputValue, conversationHistory);
      const assistantMessage = {
        role: 'assistant',
        content: response.data.answer
      };
      setMessages(prev => [...prev, assistantMessage]);
      
      // Save assistant response to database
      await pdfAPI.saveChatMessage(metadataId, 'assistant', assistantMessage.content);
    } catch (error) {
      console.error('Chat error:', error);
      let errorContent = 'Sorry, I encountered an error. Please try again.';
      
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          errorContent = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          errorContent = error.response.data.detail.map(e => e.msg).join(', ');
        }
      }
      
      const errorMessage = {
        role: 'assistant',
        content: errorContent
      };
      setMessages(prev => [...prev, errorMessage]);
      
      // Save error message to database
      await pdfAPI.saveChatMessage(metadataId, 'assistant', errorMessage.content);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSummarize = async () => {
    if (isSummarizing) return;
    
    setIsSummarizing(true);
    try {
      const response = await pdfAPI.summarize({ document_id: metadataId });
      setSummary(response.data.summary);
      setShowSummary(true);
    } catch (error) {
      console.error('Summarization error:', error);
      alert('Failed to generate summary. Please try again.');
    } finally {
      setIsSummarizing(false);
    }
  };

  const handleClearHistory = async () => {
    try {
      await pdfAPI.clearChatHistory(metadataId);
      setMessages([]);
      setIsExtracted(false);
      hasExtractedRef.current = false;
      setClearConfirm(false);
      // Re-extract and show welcome message
      extractChunks();
    } catch (error) {
      alert('Failed to clear history: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <button onClick={() => navigate('/dashboard')} className="back-button">
          ← Back
        </button>
        <div className="chat-title">
          <h2>📄 {filename}</h2>
          <p>Ask questions about this document</p>
        </div>
        <div className="chat-actions">
          <button 
            onClick={handleSummarize} 
            disabled={isSummarizing || !isExtracted}
            className="btn-summarize"
            title="Generate AI summary of this document"
          >
            {isSummarizing ? '⏳ Summarizing...' : '📝 Summarize'}
          </button>
          <button 
            onClick={() => setClearConfirm(true)} 
            className="btn-clear"
            title="Clear chat history"
            disabled={messages.length === 0}
          >
            🗑️ Clear History
          </button>
        </div>
      </div>

      {showSummary && summary && (
        <div className="summary-panel">
          <div className="summary-header">
            <h3>📋 Document Summary</h3>
            <button onClick={() => setShowSummary(false)} className="close-btn">×</button>
          </div>
          <div className="summary-content">
            {summary}
          </div>
        </div>
      )}

      <div className="chat-messages">
        {isExtracting && (
          <div className="message assistant">
            <div className="message-content">
              <div className="loading-spinner"></div>
              Processing PDF and creating embeddings...
            </div>
          </div>
        )}
        
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <div className="message-content">
              {typeof message.content === 'string' 
                ? message.content 
                : JSON.stringify(message.content)
              }
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message assistant">
            <div className="message-content">
              <div className="loading-spinner"></div>
              Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="chat-input-form">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={isExtracted ? "Ask a question about this PDF..." : "Processing PDF..."}
          disabled={isLoading || !isExtracted}
          className="chat-input"
        />
        <button 
          type="submit" 
          disabled={isLoading || !isExtracted || !inputValue.trim()}
          className="btn-send"
        >
          Send
        </button>
      </form>

      {/* Clear History Confirmation Modal */}
      {clearConfirm && (
        <div className="modal-overlay" onClick={() => setClearConfirm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Clear Chat History</h3>
            <p>Are you sure you want to clear all chat history for this document?</p>
            <p className="warning-text">This action cannot be undone.</p>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setClearConfirm(false)}>Cancel</button>
              <button className="btn-delete-confirm" onClick={handleClearHistory}>Clear History</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chat;
