import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { authAPI } from "../api/api";

export default function OAuthSuccess() {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout } = useAuth(); // optional safety

  useEffect(() => {
    const handleOAuth = async () => {
      const params = new URLSearchParams(location.search);
      const token = params.get("token");

      if (!token) {
        navigate("/login");
        return;
      }

      // ✅ Store under correct key
      localStorage.setItem("access_token", token);

      try {
        // Validate token and load user
        const res = await authAPI.me();
        if (res.data) {
          navigate("/dashboard");
        } else {
          logout();
          navigate("/login");
        }
      } catch {
        logout();
        navigate("/login");
      }
    };

    handleOAuth();
  }, [location, navigate, logout]);

  return <div>Logging you in...</div>;
}