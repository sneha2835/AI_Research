import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import PasswordInput from './PasswordInput';
import SocialAuthButtons from './SocialAuthButtons';
import './common.css';
import './Login.css';

const Register = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);

    try {
      await register(name, email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-wrapper register-view">
      <div className="login-hero">
        <div className="hero-inner">
          <div className="hero-logo">🧬</div>
          <h1>Set up your research workspace</h1>
          <p>
            Bring every paper, annotation, and conversation into a single hub. Collaborate with your lab,
            surface hidden insights, and let Groq turbocharge your literature review.
          </p>
          <div className="hero-callout">
            <strong>Your new toolkit includes:</strong>
            <ul>
              <li>Unlimited PDF uploads with instant chunking</li>
              <li>Persistent chat memory for deeper follow-ups</li>
              <li>Shareable threads to keep teams aligned</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="login-dialog register-dialog">
        <div className="dialog-header">
          <div className="dialog-logo">🧪</div>
          <div>
            <h2>Create your account</h2>
            <span>Start with a free workspace in minutes</span>
          </div>
        </div>

        {error && <div className="dialog-error">{error}</div>}

        <form className="dialog-form" onSubmit={handleSubmit}>
          <label className="field" htmlFor="name">
            <span>Full name</span>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              minLength={3}
              placeholder="e.g. Dr. Priya Sharma"
              autoComplete="name"
            />
          </label>

          <label className="field" htmlFor="email">
            <span>Email address</span>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@researchlab.com"
              autoComplete="email"
            />
          </label>

          <PasswordInput
            id="password"
            label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            placeholder="At least 8 characters"
            autoComplete="new-password"
          />
          <span className="field-hint">Use a mix of letters, numbers, and symbols.</span>

          <PasswordInput
            id="confirmPassword"
            label="Confirm password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            placeholder="Re-enter your password"
            autoComplete="new-password"
          />

          <div className="dialog-policy">
            By creating an account you agree to our <a href="#">Terms</a> and <a href="#">Privacy Policy</a>.
          </div>

          <button type="submit" className="btn-primary" disabled={isLoading}>
            {isLoading ? 'Creating your workspace…' : 'Create account'}
          </button>
        </form>

        <SocialAuthButtons mode="signup" />

        <div className="dialog-links">
          <span>Already a member? <Link to="/login">Sign in</Link></span>
        </div>
      </div>
    </div>
  );
};

export default Register;
