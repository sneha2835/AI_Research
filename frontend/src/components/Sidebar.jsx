import { NavLink } from "react-router-dom";
import "./Sidebar.css";

export default function Sidebar() {
  return (
    <aside className="sidebar">

      {/* LOGO SECTION */}
      <div className="sidebar-logo">
        <div className="logo-badge">RC</div>
        <span className="brand-name">ResearchCompanion</span>
      </div>

      {/* NAV LINKS */}
      <nav className="sidebar-nav">
        <NavLink 
          to="/dashboard"
          className={({ isActive }) => isActive ? "active" : ""}
        >
          Dashboard
        </NavLink>

        <NavLink 
          to="/papers"
          className={({ isActive }) => isActive ? "active" : ""}
        >
          Search Papers
        </NavLink>

        <NavLink 
          to="/pdfs"
          className={({ isActive }) => isActive ? "active" : ""}
        >
          Upload PDFs
        </NavLink>

        <NavLink 
          to="/profile"
          className={({ isActive }) => isActive ? "active" : ""}
        >
          My Profile
        </NavLink>
      </nav>

    </aside>
  );
}