import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import './Profile.css';

const Profile = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState({
    email: '',
    name: '',
  });

  const [passwords, setPasswords] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  // ==================================================
  // Sync user → local state
  // ==================================================
  useEffect(() => {
    if (user) {
      setProfile({
        email: user.email || '',
        name: user.name || '',
      });
    }
  }, [user]);

  // ==================================================
  // Handlers
  // ==================================================
  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfile((prev) => ({ ...prev, [name]: value }));
  };

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswords((prev) => ({ ...prev, [name]: value }));
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setIsSaving(true);
    setMessage({ type: '', text: '' });

    try {
      // 🔒 Backend update API can be wired later
      // await authAPI.updateProfile(profile);

      setMessage({ type: 'success', text: 'Profile updated successfully!' });
      setIsEditing(false);

      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to update profile',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();

    if (passwords.newPassword !== passwords.confirmPassword) {
      setMessage({ type: 'error', text: 'Passwords do not match' });
      return;
    }

    if (passwords.newPassword.length < 8) {
      setMessage({
        type: 'error',
        text: 'Password must be at least 8 characters',
      });
      return;
    }

    setIsSaving(true);
    setMessage({ type: '', text: '' });

    try {
      // 🔒 Backend password change API can be wired later
      // await authAPI.changePassword(passwords);

      setMessage({ type: 'success', text: 'Password changed successfully!' });
      setPasswords({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });

      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to change password',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteAccount = () => {
    if (
      window.confirm(
        'Are you sure you want to delete your account? This action cannot be undone.'
      )
    ) {
      alert('Account deletion functionality coming soon');
    }
  };

  // ==================================================
  // Render
  // ==================================================
  return (
    <div className="profile-container">
      {/* Header */}
      <div className="profile-header">
        <button onClick={() => navigate('/dashboard')} className="back-button">
          ← Back to Dashboard
        </button>
        <h1>Account Settings</h1>
      </div>

      {/* Message */}
      {message.text && (
        <div className={`message ${message.type}`}>{message.text}</div>
      )}

      <div className="profile-content">
        {/* Profile Information */}
        <div className="settings-card">
          <div className="card-header">
            <h2>Profile Information</h2>
            {!isEditing && (
              <button className="btn-edit" onClick={() => setIsEditing(true)}>
                ✏️ Edit
              </button>
            )}
          </div>

          <form onSubmit={handleProfileSubmit}>
            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email"
                name="email"
                value={profile.email}
                onChange={handleProfileChange}
                disabled={!isEditing}
                className="form-input"
              />
            </div>

            <div className="form-group">
              <label>Full Name</label>
              <input
                type="text"
                name="name"
                value={profile.name}
                onChange={handleProfileChange}
                disabled={!isEditing}
                className="form-input"
              />
            </div>

            {isEditing && (
              <div className="form-actions">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => {
                    setIsEditing(false);
                    setProfile({
                      email: user?.email || '',
                      name: user?.name || '',
                    });
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-save"
                  disabled={isSaving}
                >
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            )}
          </form>
        </div>

        {/* Change Password */}
        <div className="settings-card">
          <div className="card-header">
            <h2>Change Password</h2>
          </div>

          <form onSubmit={handlePasswordSubmit}>
            <div className="form-group">
              <label>Current Password</label>
              <input
                type="password"
                name="currentPassword"
                value={passwords.currentPassword}
                onChange={handlePasswordChange}
                className="form-input"
                required
              />
            </div>

            <div className="form-group">
              <label>New Password</label>
              <input
                type="password"
                name="newPassword"
                value={passwords.newPassword}
                onChange={handlePasswordChange}
                className="form-input"
                required
                minLength={8}
              />
              <span className="form-hint">Minimum 8 characters</span>
            </div>

            <div className="form-group">
              <label>Confirm New Password</label>
              <input
                type="password"
                name="confirmPassword"
                value={passwords.confirmPassword}
                onChange={handlePasswordChange}
                className="form-input"
                required
              />
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={
                isSaving ||
                !passwords.currentPassword ||
                !passwords.newPassword
              }
            >
              {isSaving ? 'Updating...' : 'Update Password'}
            </button>
          </form>
        </div>

        {/* Danger Zone */}
        <div className="settings-card danger-zone">
          <div className="card-header">
            <h2>Danger Zone</h2>
          </div>

          <div className="danger-content">
            <div className="danger-info">
              <h3>Delete Account</h3>
              <p>
                Once you delete your account, there is no going back. Please be
                certain.
              </p>
            </div>
            <button className="btn-danger" onClick={handleDeleteAccount}>
              Delete Account
            </button>
          </div>
        </div>

        {/* Logout */}
        <div className="settings-card">
          <button
            className="btn-logout"
            onClick={() => {
              logout();
              navigate('/login');
            }}
          >
            🚪 Logout
          </button>
        </div>
      </div>
    </div>
  );
};

export default Profile;
