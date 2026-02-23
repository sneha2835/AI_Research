import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import PublicNavbar from "../components/PublicNavbar";
import "./Auth.css";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const API_BASE =
    import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!email.trim() || !password.trim()) {
      setError("Please enter both email and password.");
      return;
    }

    setLoading(true);

    try {
      await login(email.trim(), password);
      navigate("/dashboard");
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
        "Invalid email or password"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    window.location.href = `${API_BASE}/auth/google/login`;
  };

  return (
    <>
      <PublicNavbar />

      <div className="auth-wrapper">
        <div className="auth-card">
          <h2>Welcome Back</h2>
          <p className="auth-sub">Login to continue</p>

          {error && <div className="auth-error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <button type="submit" disabled={loading}>
              {loading ? "Logging in..." : "Login"}
            </button>

            <button
              type="button"
              onClick={handleGoogleLogin}
              style={{ marginTop: "12px" }}
            >
              Continue with Google
            </button>
          </form>

          <div className="auth-footer">
            Don’t have an account?{" "}
            <span
              onClick={() => navigate("/register")}
              style={{ cursor: "pointer", color: "#6c63ff" }}
            >
              Register
            </span>
          </div>
        </div>
      </div>
    </>
  );
}