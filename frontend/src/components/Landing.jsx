import React from 'react';
import { Link } from 'react-router-dom';
import './common.css';
import './Landing.css';

const Landing = () => {
  return (
    <div className="landing">
      <header className="landing-header">
        <div className="landing-header__logo">
          <div className="logo-mark">🧠</div>
          <span className="logo-word">Research Companion</span>
        </div>
        <nav className="landing-nav">
          <a href="#features">Features</a>
          <a href="#how-it-works">Workflow</a>
          <a href="#uses">Use cases</a>
          <a href="#support">Support</a>
        </nav>
        <div className="landing-header__actions">
          <Link to="/login" className="btn-outline">Login</Link>
          <Link to="/register" className="btn-solid">Sign Up</Link>
        </div>
      </header>

      <main className="landing-hero">
        <section className="hero-visual" aria-hidden="true">
          <div className="burrow">
            <div className="burrow__hole burrow__hole--lg" />
            <div className="burrow__hole" />
            <div className="burrow__hole burrow__hole--md" />
            <div className="burrow__hole burrow__hole--small" />
            <div className="burrow__hole burrow__hole--tiny" />
          </div>
          <div className="rabbit">
            <div className="rabbit__ears" />
            <div className="rabbit__head">
              <span className="rabbit__eyes" />
              <span className="rabbit__nose" />
            </div>
            <div className="rabbit__shadow" />
          </div>
        </section>

        <section className="hero-copy">
          <h1 className="hero-title">Follow your curiosity</h1>
          <p className="hero-subtitle">
            Keep your literature review fast, collaborative, and deeply insightful. Dive into
            lightning-speed document understanding powered by Groq and retrieval augmented intelligence.
          </p>
          <div className="hero-actions">
            <Link to="/register" className="btn-solid btn-solid--xl">Get started</Link>
            <Link to="/login" className="btn-outline btn-outline--ghost">Preview the demo</Link>
          </div>
          <div id="features" className="hero-feature-grid">
            <div className="feature-card">
              <span className="feature-icon">⚡</span>
              <div className="feature-text">
                <strong>Groq-speed answers</strong>
                <span>Milliseconds to insight, even on 200-page PDFs.</span>
              </div>
            </div>
            <div className="feature-card">
              <span className="feature-icon">🔍</span>
              <div className="feature-text">
                <strong>Context-aware chat</strong>
                <span>Remembers the conversation, not just your questions.</span>
              </div>
            </div>
            <div className="feature-card">
              <span className="feature-icon">🛡</span>
              <div className="feature-text">
                <strong>Secure by default</strong>
                <span>Encrypted auth, private document spaces, audit-ready.</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer id="support" className="landing-footer">
        <div>
          <span>© {new Date().getFullYear()} Research Companion</span>
          <span className="dot" />
          <a href="mailto:support@researchcompanion.ai">support@researchcompanion.ai</a>
        </div>
        <div className="footer-links">
          <a href="#how-it-works">Docs</a>
          <a href="#uses">Privacy</a>
          <a href="#features">Roadmap</a>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
