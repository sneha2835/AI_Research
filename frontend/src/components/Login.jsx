import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import PasswordInput from './PasswordInput';
import SocialAuthButtons from './SocialAuthButtons';
import './common.css';
import './Login.css';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-wrapper">
      <div className="login-hero">
        <div className="hero-inner">
          <div className="hero-logo">🔬</div>
          <h1>Research AI Companion</h1>
          <p>
            Keep your literature search quick, organized, and collaborative. Upload PDFs, chat with documents,
            and uncover insights at Groq speed.
          </p>
          <div className="hero-callout">
            <strong>Why teams switch:</strong>
            <ul>
              <li>Semantic search across every paper</li>
              <li>Conversational memory that sticks</li>
              <li>Enterprise security out of the box</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="login-dialog">
        <div className="dialog-header">
          <div className="dialog-logo">🔬</div>
          <div>
            <h2>Sign in</h2>
            <span>/ Sign up</span>
          </div>
        </div>

        {error && <div className="dialog-error">{error}</div>}

        <form className="dialog-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Email address</span>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="name@researchlab.com"
              autoComplete="email"
            />
          </label>

          <PasswordInput
            id="password"
            label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="Enter your password"
            autoComplete="current-password"
          />

          <div className="dialog-links">
            <span>
              Don't have an account? <Link to="/register">Sign up</Link>
            </span>
            <a href="#">Forgot password?</a>
          </div>

          <button type="submit" className="btn-primary" disabled={isLoading}>
            {isLoading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <SocialAuthButtons mode="signin" />
      </div>
    </div>
  );
};

export default Login;