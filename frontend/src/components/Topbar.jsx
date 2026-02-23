import { useAuth } from "../auth/AuthContext"; 
import "./Topbar.css";

export default function Topbar() {
  const { user, logout } = useAuth();

  return (
    <header className="topbar">
      <div></div>

      <div className="topbar-right">
        <span className="user-email">
          {user?.email}
        </span>
        <button onClick={logout}>Logout</button>
      </div>
    </header>
  );
}