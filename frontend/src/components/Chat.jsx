import React, { useState, useEffect, useRef } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { pdfAPI } from '../services/api';
import './common.css';
import './Chat.css';

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
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadChatHistory();
    extractChunks();
  }, [metadataId]);

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
    if (isExtracted || messages.length > 0) return;
    
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
      const errorMessage = {
        role: 'assistant',
        content: error.response?.data?.detail || 'Sorry, I encountered an error. Please try again.'
      };
      setMessages(prev => [...prev, errorMessage]);
      
      // Save error message to database
      await pdfAPI.saveChatMessage(metadataId, 'assistant', errorMessage.content);
    } finally {
      setIsLoading(false);
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
      </div>

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
              {message.content}
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
    </div>
  );
};

export default Chat;
