import { Link } from "react-router-dom";
import "./PublicNavbar.css";

export default function PublicNavbar() {
  return (
    <nav className="public-nav">

      {/* LOGO */}
      <Link to="/" className="nav-logo" style={{ textDecoration: "none", color: "inherit" }}>
        <div className="logo-badge">RC</div>
        <span>ResearchCompanion</span>
      </Link>

      {/* ACTIONS */}
      <div className="nav-actions">
        <Link to="/login" className="nav-login">
          Login
        </Link>

        <Link to="/register" className="nav-signup">
          Sign Up
        </Link>
      </div>

    </nav>
  );
}