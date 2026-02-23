import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import ProtectedRoute from "./auth/ProtectedRoute";
import Layout from "./components/Layout";

import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Papers from "./pages/Papers";
import PDFs from "./pages/PDFs";
import Profile from "./pages/Profile";
import Landing from "./pages/Landing";
import ResumeChat from "./pages/ResumeChat";
import OAuthSuccess from "./pages/OAuthSuccess";
import { ThemeProvider } from "./theme/ThemeContext";

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
      <BrowserRouter>
        <Routes>

          {/* PUBLIC ROUTES */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/oauth-success" element={<OAuthSuccess />} />

          {/* PROTECTED ROUTES */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/papers"
            element={
              <ProtectedRoute>
                <Layout>
                  <Papers />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/pdfs"
            element={
              <ProtectedRoute>
                <Layout>
                  <PDFs />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Layout>
                  <Profile />
                </Layout>
              </ProtectedRoute>
            }
          />

          <Route
            path="/resume-chat/:documentId"
            element={
                <ProtectedRoute>
                <ResumeChat />
                </ProtectedRoute>
            }
          />


        </Routes>
      </BrowserRouter>
      </ThemeProvider>
    </AuthProvider>
  );
}
