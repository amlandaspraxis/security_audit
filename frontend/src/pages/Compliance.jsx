import React, { useState, useEffect } from 'react';
import { ShieldAlert, BookOpen, CheckCircle, ShieldCheck, Loader2 } from 'lucide-react';

export default function Compliance({ user, apiCall }) {
  const [frameworks, setFrameworks] = useState([]);
  const [selectedFramework, setSelectedFramework] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatingId, setUpdatingId] = useState(null);

  const loadFrameworks = async () => {
    try {
      const res = await apiCall('/api/compliance/frameworks');
      const data = await res.json();
      setFrameworks(data);
      
      // Keep selected framework updated or default to first
      if (selectedFramework) {
        const updated = data.find(f => f.id === selectedFramework.id);
        setSelectedFramework(updated || data[0]);
      } else if (data.length > 0) {
        setSelectedFramework(data[0]);
      }
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFrameworks();
  }, []);

  const handleStateChange = async (controlId, nextState) => {
    setUpdatingId(controlId);
    setError(null);
    try {
      const res = await apiCall(`/api/compliance/controls/${controlId}`, {
        method: 'PUT',
        body: JSON.stringify({ state: nextState })
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to update control state');
      }

      await loadFrameworks();
    } catch (err) {
      setError(err.message);
    } finally {
      setUpdatingId(null);
    }
  };

  // Helper to calculate progress percentage
  const getProgress = (framework) => {
    if (!framework || !framework.controls || framework.controls.length === 0) return 0;
    const compliant = framework.controls.filter(c => c.state === 'compliant').length;
    return Math.round((compliant / framework.controls.length) * 100);
  };

  const isMutationAllowed = ['admin', 'auditor'].includes(user.role);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
        <Loader2 className="logo-icon" style={{ animation: 'spin 1s linear infinite' }} size={32} />
      </div>
    );
  }

  return (
    <div>
      {error && (
        <div className="glass-card" style={{ padding: '1rem 1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem', borderLeft: '4px solid var(--error)', marginBottom: '1.5rem', color: '#f87171', fontSize: '0.9rem' }}>
          <ShieldAlert size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Tabs navigation for Framework selection */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
        {frameworks.map((fw) => (
          <button 
            key={fw.id}
            className={`btn ${selectedFramework?.id === fw.id ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setSelectedFramework(fw)}
          >
            <BookOpen size={16} />
            <span>{fw.name} (v{fw.version})</span>
          </button>
        ))}
      </div>

      {selectedFramework && (
        <div>
          {/* Framework Overview Header */}
          <div className="glass-card" style={{ marginBottom: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <h3 style={{ fontSize: '1.3rem', color: '#fff', marginBottom: '0.5rem' }}>{selectedFramework.name} Framework Controls</h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '700px' }}>{selectedFramework.description}</p>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Compliance Progress</span>
                <div style={{ fontSize: '2rem', fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--success)', marginTop: '0.25rem' }}>
                  {getProgress(selectedFramework)}%
                </div>
              </div>
            </div>

            <div className="progress-bar-bg" style={{ height: '10px', borderRadius: '5px' }}>
              <div className="progress-bar-fill" style={{ width: `${getProgress(selectedFramework)}%`, background: 'var(--success)' }}></div>
            </div>
          </div>

          {/* Controls List table */}
          <div className="glass-card">
            <h3 style={{ fontSize: '1.1rem', marginBottom: '1.5rem' }}>Security Controls Checklist</h3>
            <div className="table-container">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Control ID</th>
                    <th>Title</th>
                    <th>Requirement Description</th>
                    <th>Implementation State</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedFramework.controls && selectedFramework.controls.length > 0 ? (
                    selectedFramework.controls.map((control) => (
                      <tr key={control.id}>
                        <td>
                          <strong style={{ color: 'var(--primary)', fontFamily: 'monospace' }}>{control.section_code}</strong>
                        </td>
                        <td style={{ color: '#fff', fontWeight: 600, fontSize: '0.9rem' }}>{control.title}</td>
                        <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{control.description}</td>
                        <td>
                          {isMutationAllowed ? (
                            <select 
                              className="form-input" 
                              style={{ width: '160px', padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}
                              value={control.state}
                              onChange={(e) => handleStateChange(control.id, e.target.value)}
                              disabled={updatingId === control.id}
                            >
                              <option value="not_started">Not Started</option>
                              <option value="implementing">Implementing</option>
                              <option value="compliant">Compliant</option>
                              <option value="non_compliant">Non Compliant</option>
                            </select>
                          ) : (
                            <span className={`badge badge-${control.state.toLowerCase()}`}>
                              {control.state.replace('_', ' ')}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                        No controls found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
