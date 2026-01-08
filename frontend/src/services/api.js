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
  ask: (payload) => api.post('/pdf/ask', payload),
  askWithHistory: (metadata_id, query, conversationHistory = '', nResults = 5) =>
    api.post('/pdf/ask', { 
      metadata_id, 
      query, 
      conversation_history: conversationHistory, 
      n_results: nResults 
    }),
  summarize: (text) => api.post('/pdf/summarize', { text }),
  deletePDF: (metadataId) => api.delete(`/pdf/delete/${metadataId}`),
  
  // Chat history APIs
  saveChatMessage: (metadata_id, role, content) =>
    api.post('/pdf/chat/save', { metadata_id, role, content }),
  getChatHistory: (metadataId) => api.get(`/pdf/chat/history/${metadataId}`),
  clearChatHistory: (metadataId) => api.delete(`/pdf/chat/history/${metadataId}`),
};

// Papers/arXiv APIs
export const papersAPI = {
  getRecent: (limit = 10) => api.get('/papers/recent', { params: { limit } }),
  getPaperDetails: (paperId) => api.get(`/papers/${paperId}`),
  search: (query, limit = 5) => 
    api.get('/papers/search', { params: { q: query, limit } }),
  trackView: (paperId) => api.post(`/papers/view/${paperId}`),
  processArxiv: (paperId) => api.post(`/papers/process/${paperId}`),
  getRecentlyViewed: (limit = 10) => 
    api.get('/papers/recently-viewed', { params: { limit } }),
  testChroma: (query = 'LLM', limit = 5) =>
    api.get('/papers/test/chroma', { params: { q: query, limit } }),
};

export default api;