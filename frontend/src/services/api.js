import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});

// ==================================================
// 🔐 Attach JWT automatically
// ==================================================
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ==================================================
// 🔑 Auth APIs
// ==================================================

export const authAPI = {
  register: ({ name, email, password }) =>
    api.post("/register", { name, email, password }),

  login: ({ email, password }) => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);

    return api.post("/token", form, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });
  },

  getCurrentUser: () => api.get("/users/me"),
};

// ==================================================
// 📄 PDF APIs (Uploads + arXiv documents)
// ==================================================

export const pdfAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/pdf/upload", formData);
  },

  getMyUploads: () => api.get("/pdf/my_uploads"),

  ask: (document_id, query, n_results = 5) =>
    api.post("/pdf/ask", {
      document_id,
      query,
      n_results,
    }),

  summarize: (document_id) =>
    api.post("/pdf/summarize", { document_id }),

  deletePDF: (document_id) =>
    api.delete(`/pdf/delete/${document_id}`),

  // --------------------------
  // 💬 Chat APIs
  // --------------------------
  getChatHistory: (document_id) =>
    api.get(`/pdf/chat/history/${document_id}`),

  saveChat: (payload) =>
    api.post("/pdf/chat/save", payload),
};

// ==================================================
// 📚 arXiv / Papers APIs
// ==================================================

export const papersAPI = {
  getRecent: (limit = 10) =>
    api.get("/papers/recent", { params: { limit } }),

  search: (query, limit = 5) =>
    api.get("/papers/search", { params: { q: query, limit } }),

  getPaperDetails: (paperId) =>
    api.get(`/papers/${paperId}`),

  analyzePaper: (paperId) =>
    api.post(`/papers/analyze/${paperId}`),

  getRecentlyViewed: (limit = 10) =>
    api.get("/papers/recently-viewed", { params: { limit } }),
};

export default api;
