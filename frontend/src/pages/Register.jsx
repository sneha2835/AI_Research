import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import PublicNavbar from "../components/PublicNavbar";
import "./Auth.css";

export default function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await register(name, email, password);
      navigate("/login"); // Redirect after successful registration
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
        "Registration failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <PublicNavbar />

      <div className="auth-wrapper">
        <div className="auth-card">
          <h2>Create Account</h2>
          <p className="auth-sub">
            Start your AI research journey
          </p>

          {error && <div className="auth-error">{error}</div>}

          <form onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Full Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />

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
              {loading ? "Creating account..." : "Register"}
            </button>
          </form>

          <div className="auth-footer">
            Already have an account?{" "}
            <span
              onClick={() => navigate("/login")}
              style={{ cursor: "pointer", color: "#6c63ff" }}
            >
              Login
            </span>
          </div>
        </div>
      </div>
    </>
  );
}