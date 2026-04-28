import { Link } from "react-router-dom";
import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import PublicNavbar from "../components/PublicNavbar";

export default function Landing() {
  const [showDemo, setShowDemo] = useState(false);

  // Close modal with ESC key
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === "Escape") {
        setShowDemo(false);
      }
    };

    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, []);

  // ⭐ Ensure modal always opens at top of viewport
  useEffect(() => {
    if (showDemo) {
      window.scrollTo({ top: 0, behavior: "instant" });
    }
  }, [showDemo]);

  const modalRoot = document.getElementById("modal-root");

  return (
    <div className="landing-wrapper">

      {/* NAVBAR */}
      <PublicNavbar />

      {/* HERO */}
      <section className="hero">

        <div className="hero-left">
          <h1>
            Where Research Meets <span>Intelligence</span>
          </h1>

          <p className="hero-sub">
            AI-Powered Scientific Research Companion for Literature Review and Knowledge Discovery.
          </p>

          <div className="hero-buttons">
            <Link to="/register" className="btn-primary">
              Get Started
            </Link>

            <button
              className="btn-secondary"
              onClick={() => setShowDemo(true)}
            >
              Watch Demo
            </button>
          </div>
        </div>

        {/* RIGHT SIDE */}
        <div className="hero-right">
          <div className="motion-glow"></div>

          <div className="motion-card">
            <div className="card-header">
              <span className="dot red"></span>
              <span className="dot yellow"></span>
              <span className="dot green"></span>
            </div>

            <div className="card-search">
              🔎 Attention Mechanism
            </div>

            <div className="card-body">
              <h3>Attention Is All You Need</h3>
              <p>arXiv · Neural Networks · 2.1k citations</p>

              <button className="analyze-btn">
                Analyze
              </button>
            </div>
          </div>
        </div>

      </section>

      {/* FEATURES */}
      <section className="features">

        <div className="feature-card">
          <div className="icon">🚀</div>
          <h3>Intelligent Search</h3>
          <p>
            Quickly find relevant papers using advanced AI filtering and ranking.
          </p>
        </div>

        <div className="feature-card">
          <div className="icon">🧠</div>
          <h3>Automated Analysis</h3>
          <p>
            Extract insights, methods, datasets, and key contributions instantly.
          </p>
        </div>

        <div className="feature-card">
          <div className="icon">📊</div>
          <h3>Data Extraction</h3>
          <p>
            Effortlessly extract tables, citations, and structured data from PDFs.
          </p>
        </div>

      </section>

      {/* DEMO MODAL */}
      {showDemo && modalRoot &&
        createPortal(
          <div
            className="demo-overlay"
            onClick={() => setShowDemo(false)}
          >
            <div
              className="demo-modal"
              onClick={(e) => e.stopPropagation()}
            >

              <button
                className="demo-close"
                onClick={() => setShowDemo(false)}
              >
                ✕
              </button>

              <video
                className="demo-video"
                controls
                autoPlay
              >
                <source src="/Major_Proj_Demo.mp4" type="video/mp4" />
                Your browser does not support the video tag.
              </video>

            </div>
          </div>,
          modalRoot
        )}

    </div>
  );
}