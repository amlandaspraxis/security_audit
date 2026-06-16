import React, { useState } from 'react';
import { ShieldAlert, AlertOctagon, KeyRound } from 'lucide-react';

export default function Login({ setToken, apiCall, forceChangePassword = false, onPasswordResetSuccess }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  
  // Password Reset fields
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString()
      });

      if (res.status === 429) {
        throw new Error('Too many login attempts. Please wait a minute and try again.');
      }

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Login failed. Please verify credentials.');
      }

      // Success - set token in parent state
      setToken(data.access_token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordReset = async (e) => {
    e.preventDefault();
    setError(null);

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      const res = await apiCall('/api/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to update password. Password must be complex.');
      }

      if (onPasswordResetSuccess) {
        onPasswordResetSuccess();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (forceChangePassword) {
    return (
      <div className="login-wrapper">
        <div className="glass-card login-card" style={{ maxWidth: '480px' }}>
          <KeyRound size={40} className="logo-icon" style={{ margin: '0 auto 1.5rem auto' }} />
          <h2 style={{ marginBottom: '0.5rem' }}>Change Initial Password</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '2rem' }}>
            A password reset is required on your first login for account hardening.
          </p>

          {error && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: 'var(--radius-md)',
              padding: '0.75rem',
              color: '#f87171',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.85rem',
              marginBottom: '1.5rem',
              textAlign: 'left'
            }}>
              <AlertOctagon size={16} style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handlePasswordReset}>
            <div className="form-group" style={{ textAlign: 'left' }}>
              <label>Current Credentials Password</label>
              <input 
                type="password" 
                className="form-input" 
                value={currentPassword}
                onChange={e => setCurrentPassword(e.target.value)}
                required
              />
            </div>

            <div className="form-group" style={{ textAlign: 'left' }}>
              <label>New Password</label>
              <input 
                type="password" 
                className="form-input" 
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                placeholder="Must be complex (8+ chars, mix case, num, spec)"
                required
              />
            </div>

            <div className="form-group" style={{ textAlign: 'left' }}>
              <label>Confirm New Password</label>
              <input 
                type="password" 
                className="form-input" 
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                required
              />
            </div>

            <button 
              type="submit" 
              className="btn btn-primary" 
              style={{ width: '100%', justifyContent: 'center', marginTop: '1rem' }}
              disabled={loading}
            >
              {loading ? 'Updating Password...' : 'Update & Proceed'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="login-wrapper">
      <div className="glass-card login-card">
        <div className="logo login-logo" style={{ justifyContent: 'center', flexDirection: 'column', gap: '0.5rem' }}>
          <ShieldAlert className="logo-icon" size={36} />
          <span style={{ fontSize: '1.5rem', lineHeight: '1.2' }}>Security Audit & Compliance Platform</span>
        </div>

        <h3 style={{ marginBottom: '1.5rem', fontSize: '1.2rem' }}>Authenticate Session</h3>

        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '0.75rem',
            color: '#f87171',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.85rem',
            marginBottom: '1.5rem',
            textAlign: 'left'
          }}>
            <AlertOctagon size={16} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin}>
          <div className="form-group" style={{ textAlign: 'left' }}>
            <label>Username</label>
            <input 
              type="text" 
              className="form-input" 
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Enter system username"
              required 
            />
          </div>

          <div className="form-group" style={{ textAlign: 'left' }}>
            <label>Password</label>
            <input 
              type="password" 
              className="form-input" 
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter security password"
              required 
            />
          </div>

          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ width: '100%', justifyContent: 'center', marginTop: '1rem' }}
            disabled={loading}
          >
            {loading ? 'Verifying...' : 'Establish Session'}
          </button>
        </form>

        <p style={{ marginTop: '2rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Security Audit & Compliance Console v1.0.0
        </p>
      </div>
    </div>
  );
}
