import axios from 'axios';

const API_BASE_URL = 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth APIs
export const authAPI = {
  register: (data) => api.post('/register', data),
  login: (data) => api.post('/token', data, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  }),
  getCurrentUser: () => api.get('/users/me'),
};

// PDF APIs
export const pdfAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/pdf/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getMyUploads: () => api.get('/pdf/my_uploads'),
  extractChunks: (metadataId) => api.get(`/pdf/extract_chunks/${metadataId}`),
  search: (query, nResults = 5) => 
    api.get('/pdf/search', { params: { query, n_results: nResults } }),
  ask: (query, nResults = 5) => 
    api.post('/pdf/ask', { query, conversation_history: '', n_results: nResults }),
  askWithHistory: (query, conversationHistory = '', nResults = 5) =>
    api.post('/pdf/ask', { query, conversation_history: conversationHistory, n_results: nResults }),
  chat: (question, nResults = 5) =>
    api.post('/pdf/chat', { question }, { params: { n_results: nResults } }),
  deletePDF: (metadataId) => api.delete(`/pdf/delete/${metadataId}`),
  
  // Chat history APIs
  saveChatMessage: (metadata_id, role, content) =>
    api.post('/pdf/chat/save', { metadata_id, role, content }),
  getChatHistory: (metadataId) => api.get(`/pdf/chat/history/${metadataId}`),
  clearChatHistory: (metadataId) => api.delete(`/pdf/chat/history/${metadataId}`),
};

export default api;
