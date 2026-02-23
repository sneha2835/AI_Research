import { useAuth } from "../auth/AuthContext";
import { useEffect, useState, useContext } from "react";
import { ThemeContext } from "../theme/ThemeContext";
import api from "../api/api";
import "./Dashboard.css";

export default function Profile() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useContext(ThemeContext);

  const [stats, setStats] = useState({
    uploads: 0,
    chats: 0,
    summaries: 0,
  });

  const [name, setName] = useState(user?.name || "");
  const [birthday, setBirthday] = useState("");

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");

  useEffect(() => {
    loadProfile();
    loadStats();
  }, []);

  /* ================= LOAD PROFILE ================= */

  const loadProfile = async () => {
    try {
      const res = await api.get("/users/me");

      setName(res.data.name || "");
      setBirthday(res.data.birthday || "");

      // ❌ DO NOT setTheme here
      // Theme is controlled ONLY by ThemeContext
    } catch (err) {
      console.error("Profile load failed", err);
    }
  };

  const loadStats = async () => {
    try {
      const res = await api.get("/dashboard/stats");
      const uploadsRes = await api.get("/pdf/my_uploads");

      setStats({
        uploads: uploadsRes.data.length,
        chats: res.data.chatCount,
        summaries: res.data.summaryCount,
      });
    } catch (err) {
      console.error("Profile stats failed", err);
    }
  };

  /* ================= SAVE PROFILE ================= */

  const handleSaveProfile = async () => {
    try {
      await api.put("/users/me", {
        name,
        birthday,
      });

      alert("Profile updated successfully!");
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to update profile.");
    }
  };

  /* ================= THEME ================= */

  const toggleTheme = async () => {
    const newTheme = theme === "dark" ? "light" : "dark";

    // update UI immediately
    setTheme(newTheme);

    try {
      await api.put("/users/me", { theme: newTheme });
    } catch (err) {
      console.error("Theme save failed");
    }
  };

  /* ================= PASSWORD ================= */

  const handleChangePassword = async () => {
    if (!oldPassword || !newPassword) {
      alert("Enter both old and new password.");
      return;
    }

    try {
      await api.put("/users/change-password", {
        old_password: oldPassword,
        new_password: newPassword,
      });

      alert("Password updated successfully!");
      setOldPassword("");
      setNewPassword("");
    } catch (err) {
      alert(err.response?.data?.detail || "Password change failed.");
    }
  };

  /* ================= DELETE ACCOUNT ================= */

  const handleDeleteAccount = async () => {
    if (!window.confirm("This will permanently delete your account. Continue?"))
      return;

    try {
      await api.delete("/users/me");
      alert("Account deleted.");
      logout();
    } catch (err) {
      alert("Account deletion failed.");
    }
  };

  /* ================= EXPORT HISTORY ================= */

  const handleExportHistory = async () => {
    try {
      const res = await api.get("/users/export-history");

      const blob = new Blob([JSON.stringify(res.data, null, 2)], {
        type: "application/json",
      });

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "chat_history.json";
      a.click();

      URL.revokeObjectURL(url);
    } catch (err) {
      alert("Export failed.");
    }
  };

  return (
    <div>
      <h1 className="dashboard-title">My Profile</h1>

      {/* ===== PERSONAL INFO ===== */}
      <div className="dashboard-panel">
        <h2 className="panel-title">Personal Information</h2>

        <SettingRow
          label="Name"
          action={
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="profile-input"
            />
          }
        />

        <SettingRow label="Email" action={<span>{user?.email}</span>} />

        <SettingRow
          label="Birthday"
          action={
            <input
              type="date"
              value={birthday}
              onChange={(e) => setBirthday(e.target.value)}
              className="profile-input"
            />
          }
        />

        <button className="analyze-btn" onClick={handleSaveProfile}>
          Save Changes
        </button>
      </div>

      {/* ===== ACTIVITY ===== */}
      <div className="dashboard-panel">
        <h2 className="panel-title">Activity</h2>

        <div className="stats-grid">
          <StatCard title="Uploads" value={stats.uploads} />
          <StatCard title="Chat Sessions" value={stats.chats} />
          <StatCard title="AI Summaries" value={stats.summaries} />
        </div>
      </div>

      {/* ===== ACCOUNT SETTINGS ===== */}
      <div className="dashboard-panel">
        <h2 className="panel-title">Account Settings</h2>

        <SettingRow
          label="Theme"
          action={
            <button className="analyze-btn" onClick={toggleTheme}>
              Switch to {theme === "dark" ? "Light" : "Dark"} Mode
            </button>
          }
        />

        <SettingRow
          label="Change Password"
          action={
            <div className="password-row">
              <input
                type="password"
                placeholder="Old password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                className="profile-input"
              />
              <input
                type="password"
                placeholder="New password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="profile-input"
              />
              <button
                className="analyze-btn"
                onClick={handleChangePassword}
              >
                Update
              </button>
            </div>
          }
        />

        <SettingRow
          label="Export Chat History"
          action={
            <button className="analyze-btn" onClick={handleExportHistory}>
              Download JSON
            </button>
          }
        />

        <SettingRow
          label="Delete Account"
          action={
            <button className="delete-btn" onClick={handleDeleteAccount}>
              Delete Account
            </button>
          }
        />

        <SettingRow
          label="Logout"
          action={
            <button className="delete-btn" onClick={logout}>
              Logout
            </button>
          }
        />
      </div>
    </div>
  );
}

/* ===== Reusable Components ===== */

function StatCard({ title, value }) {
  return (
    <div className="stat-card">
      <div className="stat-value">{value}</div>
      <div className="stat-title">{title}</div>
    </div>
  );
}

function SettingRow({ label, action }) {
  return (
    <div className="profile-row">
      <div className="profile-label">{label}</div>
      <div className="profile-action">{action}</div>
    </div>
  );
}