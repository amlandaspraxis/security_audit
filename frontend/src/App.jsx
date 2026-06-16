import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  LayoutDashboard, 
  Boxes, 
  ShieldCheck, 
  AlertTriangle, 
  LogOut, 
  User as UserIcon,
  Moon,
  Sun
} from 'lucide-react';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Assets from './pages/Assets';
import Compliance from './pages/Compliance';
import Findings from './pages/Findings';

export default function App() {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [currentView, setCurrentView] = useState('dashboard');
  const [theme, setTheme] = useState('dark');

  // Load user profile when token changes
  useEffect(() => {
    if (token) {
      fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      .then(res => {
        if (!res.ok) throw new Error('Failed to load profile');
        return res.json();
      })
      .then(data => {
        setUser(data);
        // If password reset required, it will be handled inside Login component or globally
      })
      .catch(() => {
        setToken(null);
        setUser(null);
      });
    } else {
      setUser(null);
    }
  }, [token]);

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    document.documentElement.setAttribute('data-theme', nextTheme);
  };

  const handleLogout = () => {
    setToken(null);
    setUser(null);
    setCurrentView('dashboard');
  };

  // Helper function for API calls using active session token
  const apiCall = async (url, options = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(url, { ...options, headers });
    if (response.status === 401) {
      handleLogout();
      throw new Error('Session expired');
    }
    return response;
  };

  // Auth Guard
  if (!token || !user) {
    return (
      <Login 
        setToken={setToken} 
        apiCall={apiCall} 
        onSuccess={(t) => setToken(t)} 
      />
    );
  }

  // Handle password reset lock
  if (user.must_reset_password) {
    return (
      <Login 
        setToken={setToken} 
        apiCall={apiCall} 
        forceChangePassword={true} 
        onPasswordResetSuccess={() => {
          // Refresh user profile
          apiCall('/api/auth/me')
            .then(res => res.json())
            .then(data => setUser(data));
        }}
      />
    );
  }

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="logo">
          <ShieldAlert className="logo-icon" size={28} />
          <span style={{ fontSize: '0.95rem', lineHeight: '1.2' }}>Security Audit & Compliance Platform</span>
        </div>

        <nav className="nav-list">
          <a 
            className={`nav-item ${currentView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentView('dashboard')}
          >
            <LayoutDashboard size={20} />
            <span>Dashboard</span>
          </a>
          
          <a 
            className={`nav-item ${currentView === 'assets' ? 'active' : ''}`}
            onClick={() => setCurrentView('assets')}
          >
            <Boxes size={20} />
            <span>Asset Inventory</span>
          </a>
          
          <a 
            className={`nav-item ${currentView === 'compliance' ? 'active' : ''}`}
            onClick={() => setCurrentView('compliance')}
          >
            <ShieldCheck size={20} />
            <span>Compliance Tracker</span>
          </a>
          
          <a 
            className={`nav-item ${currentView === 'findings' ? 'active' : ''}`}
            onClick={() => setCurrentView('findings')}
          >
            <AlertTriangle size={20} />
            <span>Vulnerabilities</span>
          </a>
        </nav>

        <div style={{ marginTop: 'auto' }}>
          <button 
            className="btn btn-secondary" 
            onClick={toggleTheme}
            style={{ width: '100%', justifyContent: 'center', marginBottom: '0.75rem' }}
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            <span>Toggle Theme</span>
          </button>
          
          <button 
            className="btn btn-danger" 
            onClick={handleLogout}
            style={{ width: '100%', justifyContent: 'center' }}
          >
            <LogOut size={18} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Layout Area */}
      <main className="main-content">
        <header className="dashboard-header">
          <div>
            <h1 style={{ fontSize: '1.8rem', color: 'var(--text-primary)' }}>
              {currentView === 'dashboard' && "System Security Overview"}
              {currentView === 'assets' && "Asset Directory"}
              {currentView === 'compliance' && "Security Controls Tracker"}
              {currentView === 'findings' && "Vulnerabilities & Findings Database"}
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Continuous Audit & Vulnerability Management
            </p>
          </div>

          <div className="user-badge">
            <UserIcon size={16} style={{ color: 'var(--primary)' }} />
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{user.username}</span>
            <span className="badge badge-low" style={{ fontSize: '0.7rem' }}>{user.role}</span>
          </div>
        </header>

        {/* View Router */}
        {currentView === 'dashboard' && <Dashboard user={user} apiCall={apiCall} />}
        {currentView === 'assets' && <Assets user={user} apiCall={apiCall} />}
        {currentView === 'compliance' && <Compliance user={user} apiCall={apiCall} />}
        {currentView === 'findings' && <Findings user={user} apiCall={apiCall} />}
      </main>
    </div>
  );
}
