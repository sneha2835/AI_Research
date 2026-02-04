import React, { createContext, useContext, useEffect, useState } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // -------------------------------------------
  // Load user on app start
  // -------------------------------------------
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');

      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const response = await authAPI.getMe();

        const safeUser = normalizeUser(response.data);
        setUser(safeUser);
      } catch (err) {
        console.error('Auth restore failed:', err);
        localStorage.removeItem('access_token');
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  // -------------------------------------------
  // Login
  // -------------------------------------------
  const login = async (email, password) => {
    const response = await authAPI.login(email, password);
    localStorage.setItem('access_token', response.data.access_token);

    const me = await authAPI.getMe();
    setUser(normalizeUser(me.data));
  };

  // -------------------------------------------
  // Logout
  // -------------------------------------------
  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        setUser,
        login,
        logout,
        loading,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// -------------------------------------------
// Helpers
// -------------------------------------------

function normalizeUser(raw) {
  if (!raw) return null;

  return {
    _id: raw._id,
    name: raw.name || '',
    email: raw.email || '',
  };
}

export const useAuth = () => useContext(AuthContext);
