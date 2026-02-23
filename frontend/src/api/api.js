import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

// attach token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ================= AUTH =================
export const authAPI = {
  register: (data) => api.post("/register", data),

  login: ({ email, password }) => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);

    return api.post("/token", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },

  me: () => api.get("/users/me"),
};

export default api;
