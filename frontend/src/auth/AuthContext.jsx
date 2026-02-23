import { createContext, useContext, useEffect, useState } from "react";
import { authAPI } from "../api/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const restore = async () => {
      const token = localStorage.getItem("access_token");
      if (!token) return setLoading(false);

      try {
        const res = await authAPI.me();
        setUser(res.data);
      } catch {
        localStorage.removeItem("access_token");
      } finally {
        setLoading(false);
      }
    };

    restore();
  }, []);

  const login = async (email, password) => {
    const res = await authAPI.login({ email, password });
    localStorage.setItem("access_token", res.data.access_token);

    const me = await authAPI.me();
    setUser(me.data);
  };

  const register = async (name, email, password) => {
  await authAPI.register({ name, email, password });
};


  const logout = () => {
    localStorage.removeItem("access_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{ user, login, register, logout, loading }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
