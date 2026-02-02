import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import LandingElicit from './components/LandingElicit';
import Login from './components/Login';
import Register from './components/Register';
import DashboardElicit from './components/DashboardElicit';
import Chat from './components/Chat';
import Profile from './components/Profile';
import './App.css';

const PrivateRoute = ({ children }) => {
  const { token, isLoading } = useAuth();
  
  if (isLoading) {
    return <div className="loading-screen">Loading...</div>;
  }
  
  return token ? <>{children}</> : <Navigate to="/login" />;
};

const PublicRoute = ({ children }) => {
  const { token, isLoading } = useAuth();
  
  if (isLoading) {
    return <div className="loading-screen">Loading...</div>;
  }
  
  return token ? <Navigate to="/dashboard" /> : <>{children}</>;
};

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingElicit />} />
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <Register />
          </PublicRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <PrivateRoute>
            <DashboardElicit />
          </PrivateRoute>
        }
      />
      <Route
        path="/chat/:metadataId"
        element={
          <PrivateRoute>
            <Chat />
          </PrivateRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <PrivateRoute>
            <Profile />
          </PrivateRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
