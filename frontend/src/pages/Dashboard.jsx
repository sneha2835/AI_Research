import React, { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { useNavigate } from "react-router-dom";
import api from "../api/api";
import "./Dashboard.css";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(null);

  const [stats, setStats] = useState({
    uploads: 0,
    analyzed: 0,
    chats: 0,
    summaries: 0,
  });

  const [uploads, setUploads] = useState([]);
  const [viewed, setViewed] = useState([]);
  const [published, setPublished] = useState([]);

  const [chatSessions, setChatSessions] = useState([]);
  const [summaryList, setSummaryList] = useState([]);
  const [selectedSummary, setSelectedSummary] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const uploadsRes = await api.get("/pdf/my_uploads");
      const viewedRes = await api.get("/papers/recently-viewed");
      const statsRes = await api.get("/dashboard/stats");

      let publishedData = [];

      try {
        const publishedRes = await api.get("/papers/recent");
        publishedData = publishedRes.data || [];
      } catch {}

      setUploads(uploadsRes.data || []);
      setViewed(viewedRes.data || []);
      setPublished(publishedData);

      setStats({
        uploads: statsRes.data?.uploads || 0,
        analyzed: statsRes.data?.analyzed || 0,
        chats: statsRes.data?.chatCount || 0,
        summaries: statsRes.data?.summaryCount || 0,
      });
    } catch (err) {
      console.error("Dashboard load failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleContinueLastSession = () => {
    const documentId = localStorage.getItem("last_chat_document_id");
    const title = localStorage.getItem("last_chat_paper_title");

    if (!documentId) {
      alert("No previous chat session found.");
      return;
    }

    navigate(`/resume-chat/${documentId}`, {
      state: { title },
    });
  };

  // FIXED LINK BUILDER
  const buildViewedLink = (paper) => {
    if (paper?.pdf_url) return paper.pdf_url;

    if (paper?.document_id)
      return `${API_BASE}/pdf_uploads/${paper.document_id}.pdf`;

    return null;
  };

  if (loading) {
    return <div style={{ padding: "30px" }}>Loading dashboard...</div>;
  }

  return (
    <div>
      <h1 className="dashboard-title">
        Welcome, {user?.name || user?.email?.split("@")[0]}!
      </h1>

      <p className="dashboard-sub">Your Research Control Panel</p>

      {/* STATS */}
      <div className="stats-grid">
        <StatCard
          title="PDFs Uploaded"
          value={stats.uploads}
          onClick={() => setActiveTab("uploads")}
        />

        <StatCard
          title="Papers Analyzed"
          value={stats.analyzed}
          onClick={() => setActiveTab("analyzed")}
        />

        <StatCard
          title="Chat Sessions"
          value={stats.chats}
          onClick={async () => {
            const res = await api.get("/dashboard/chat-sessions");
            setChatSessions(res.data || []);
            setActiveTab("chats");
          }}
        />

        <StatCard
          title="AI Summaries"
          value={stats.summaries}
          onClick={async () => {
            const res = await api.get("/dashboard/summaries");
            setSummaryList(res.data || []);
            setSelectedSummary(null);
            setActiveTab("summaries");
          }}
        />
      </div>

      {/* QUICK ACTIONS */}
      <div className="dashboard-panel">
        <h2 className="panel-title">Quick Actions</h2>

        <div className="actions-row">
          <button className="analyze-btn" onClick={() => navigate("/pdfs")}>
            Upload PDF
          </button>

          <button className="analyze-btn" onClick={() => navigate("/papers")}>
            Search Papers
          </button>

          <button className="analyze-btn" onClick={handleContinueLastSession}>
            Continue Last Session
          </button>
        </div>
      </div>

      {/* RECENT UPLOADS */}
      <div className="dashboard-panel">
        <h2 className="panel-title">Recent Uploads</h2>

        {uploads.length === 0 ? (
          <p>No uploads yet.</p>
        ) : (
          uploads.slice(0, 5).map((u) => (
            <a
              key={u._id}
              href={`${API_BASE}/pdf_uploads/${u._id}.pdf`}
              target="_blank"
              rel="noopener noreferrer"
              className="dashboard-item"
            >
              {u.title}
            </a>
          ))
        )}
      </div>

      {/* RECENTLY VIEWED */}
      <div className="dashboard-panel">
        <h2 className="panel-title">Recently Viewed Papers</h2>

        {viewed.length === 0 ? (
          <p>No recently viewed papers.</p>
        ) : (
          viewed.slice(0, 5).map((paper, i) => {
            const filePath = buildViewedLink(paper);

            if (!filePath) return null;

            return (
              <a
                key={paper._id || i}
                href={filePath}
                target="_blank"
                rel="noopener noreferrer"
                className="dashboard-item"
              >
                {paper.title}
              </a>
            );
          })
        )}
      </div>

      {/* RECENTLY PUBLISHED */}
      <div className="dashboard-panel">
        <h2 className="panel-title">Recently Published Papers</h2>

        {published.length === 0 ? (
          <p>No recent publications available.</p>
        ) : (
          published.slice(0, 5).map((p, i) => (
            <a
              key={i}
              href={p.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
              className="dashboard-item"
            >
              {p.title}
            </a>
          ))
        )}
      </div>

      {/* OVERLAY */}
      {activeTab && (
        <div className="overlay">
          <div className="overlay-content">
            <div className="overlay-header">
              <h2>
                {activeTab === "uploads" && "Uploaded PDFs"}
                {activeTab === "analyzed" && "Analyzed Papers"}
                {activeTab === "chats" && "Chat Sessions"}
                {activeTab === "summaries" && "AI Summaries"}
              </h2>

              <button
                className="close-btn"
                onClick={() => {
                  setActiveTab(null);
                  setSelectedSummary(null);
                }}
              >
                ✕
              </button>
            </div>

            <div className="overlay-body">
              {activeTab === "uploads" &&
                uploads.map((u) => (
                  <div key={u._id} className="list-item">
                    {u.title}
                  </div>
                ))}

              {activeTab === "analyzed" &&
                viewed.map((p, i) => (
                  <div key={i} className="list-item">
                    {p.title}
                  </div>
                ))}

              {activeTab === "chats" &&
                chatSessions.map((session) => (
                  <div
                    key={session.document_id}
                    className="list-item clickable"
                    onClick={() =>
                      navigate(`/resume-chat/${session.document_id}`, {
                        state: { title: session.title },
                      })
                    }
                  >
                    {session.title}
                  </div>
                ))}

              {activeTab === "summaries" &&
                (selectedSummary ? (
                  <div>
                    <button
                      className="analyze-btn"
                      onClick={() => setSelectedSummary(null)}
                    >
                      ← Back
                    </button>

                    <h3 style={{ marginTop: "15px" }}>
                      {selectedSummary.title}
                    </h3>

                    <StructuredSummary text={selectedSummary.content} />
                  </div>
                ) : (
                  summaryList.map((s) => (
                    <div
                      key={s.summary_id}
                      className="list-item clickable"
                      onClick={() => setSelectedSummary(s)}
                    >
                      {s.title}
                    </div>
                  ))
                ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ title, value, onClick }) {
  return (
    <div className="stat-card clickable" onClick={onClick}>
      <div className="stat-value">{value}</div>
      <div className="stat-title">{title}</div>
    </div>
  );
}

function StructuredSummary({ text }) {
  if (!text) return null;

  const sections = {};
  let currentSection = null;

  const sectionMap = {
    objective: "Objective",
    problem: "Problem Being Addressed",
    methodology: "Methodology",
    method: "Methodology",
    findings: "Key Findings",
    conclusion: "Conclusion",
    limitations: "Limitations",
  };

  text.split("\n").forEach((line) => {
    const trimmed = line.trim();
    if (!trimmed) return;

    const lower = trimmed.toLowerCase();
    const matched = Object.keys(sectionMap).find((key) =>
      lower.startsWith(key)
    );

    if (matched) {
      currentSection = sectionMap[matched];
      sections[currentSection] = trimmed.replace(/^[^:]*:/, "").trim();
    } else if (currentSection) {
      sections[currentSection] += " " + trimmed;
    }
  });

  return (
    <div style={{ marginTop: "20px" }}>
      {Object.entries(sections).map(([title, content], i) => (
        <div
          key={i}
          style={{
            background: "#f8f9fc",
            padding: "18px",
            borderRadius: "10px",
            marginBottom: "20px",
            borderLeft: "4px solid #2c6ef2",
          }}
        >
          <h4 style={{ marginBottom: "8px" }}>{title}</h4>
          <p style={{ margin: 0, lineHeight: "1.6" }}>{content}</p>
        </div>
      ))}
    </div>
  );
}