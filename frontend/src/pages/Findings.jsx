import React, { useState, useEffect } from 'react';
import { ShieldAlert, Plus, Trash2, Eye, EyeOff, CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';

export default function Findings({ user, apiCall }) {
  const [findings, setFindings] = useState([]);
  const [assets, setAssets] = useState([]);
  const [controls, setControls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Expanded card state
  const [expandedIds, setExpandedIds] = useState(new Set());

  // Add Modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [title, setTitle] = useState('');
  const [assetId, setAssetId] = useState('');
  const [controlId, setControlId] = useState('');
  const [severity, setSeverity] = useState('medium');
  const [statusVal, setStatusVal] = useState('open');
  const [description, setDescription] = useState('');
  const [remediation, setRemediation] = useState('');
  const [discoveredBy, setDiscoveredBy] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadData = async () => {
    try {
      const findingsRes = await apiCall('/api/findings');
      const findingsData = await findingsRes.json();

      const assetsRes = await apiCall('/api/assets');
      const assetsData = await assetsRes.json();

      // Retrieve all controls across frameworks
      const frameworksRes = await apiCall('/api/compliance/frameworks');
      const frameworksData = await frameworksRes.json();
      const controlsList = [];
      frameworksData.forEach(fw => {
        if (fw.controls) {
          fw.controls.forEach(c => {
            controlsList.push({ ...c, frameworkName: fw.name });
          });
        }
      });

      setFindings(findingsData);
      setAssets(assetsData);
      setControls(controlsList);
      
      if (assetsData.length > 0 && !assetId) {
        setAssetId(assetsData[0].id);
      }
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateFinding = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const res = await apiCall('/api/findings', {
        method: 'POST',
        body: JSON.stringify({
          title,
          asset_id: parseInt(assetId),
          control_id: controlId ? parseInt(controlId) : null,
          severity,
          status: statusVal,
          description,
          remediation,
          discovered_by: discoveredBy || user.username
        })
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to submit finding');
      }

      setTitle('');
      setDescription('');
      setRemediation('');
      setControlId('');
      setShowAddModal(false);
      loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpdateStatus = async (findingId, nextStatus) => {
    setError(null);
    try {
      const res = await apiCall(`/api/findings/${findingId}`, {
        method: 'PUT',
        body: JSON.stringify({ status: nextStatus })
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to update finding status');
      }

      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteFinding = async (findingId) => {
    if (!window.confirm('Are you sure you want to permanently delete this finding?')) {
      return;
    }
    setError(null);
    try {
      const res = await apiCall(`/api/findings/${findingId}`, {
        method: 'DELETE'
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to delete finding');
      }

      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const toggleExpand = (id) => {
    const next = new Set(expandedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setExpandedIds(next);
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

      <div style={{ display: 'flex', justifycontent: 'space-between', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem' }}>Security Findings & Weaknesses</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Review, assign remediations, and resolve active vulnerabilities.</p>
        </div>
        {isMutationAllowed && assets.length > 0 && (
          <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
            <Plus size={16} />
            <span>Log Vulnerability</span>
          </button>
        )}
      </div>

      <div className="glass-card">
        <h3 style={{ fontSize: '1.1rem', marginBottom: '1.5rem' }}>Active Findings Registry</h3>
        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Vulnerability</th>
                <th>Asset Name</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Control Code</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {findings.map((finding) => {
                const asset = assets.find(a => a.id === finding.asset_id);
                const control = controls.find(c => c.id === finding.control_id);
                const isExpanded = expandedIds.has(finding.id);

                return (
                  <React.Fragment key={finding.id}>
                    <tr>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <strong style={{ color: '#fff', fontSize: '0.9rem' }}>{finding.title}</strong>
                        </div>
                      </td>
                      <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        {asset ? asset.name : 'Unknown Asset'}
                      </td>
                      <td>
                        <span className={`badge badge-${finding.severity.toLowerCase()}`}>
                          {finding.severity}
                        </span>
                      </td>
                      <td>
                        {isMutationAllowed ? (
                          <select
                            className="form-input"
                            style={{ width: '130px', padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                            value={finding.status}
                            onChange={(e) => handleUpdateStatus(finding.id, e.target.value)}
                          >
                            <option value="open">Open</option>
                            <option value="in_progress">In Progress</option>
                            <option value="resolved">Resolved</option>
                            <option value="accepted_risk">Accepted Risk</option>
                          </select>
                        ) : (
                          <span className="badge badge-low" style={{ background: 'rgba(255,255,255,0.05)' }}>
                            {finding.status.replace('_', ' ')}
                          </span>
                        )}
                      </td>
                      <td style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: 'var(--primary)' }}>
                        {control ? `${control.frameworkName} ${control.section_code}` : 'None'}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <button 
                            className="btn btn-secondary" 
                            style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}
                            onClick={() => toggleExpand(finding.id)}
                            title="Toggle expanded details"
                          >
                            {isExpanded ? <EyeOff size={14} /> : <Eye size={14} />}
                          </button>
                          {isMutationAllowed && (
                            <button 
                              className="btn btn-danger" 
                              style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--error)', borderColor: 'rgba(239, 68, 68, 0.2)' }}
                              onClick={() => handleDeleteFinding(finding.id)}
                              title="Delete finding"
                            >
                              <Trash2 size={14} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>

                    {/* Expandable Details Row */}
                    {isExpanded && (
                      <tr>
                        <td colSpan="6" style={{ background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderLeft: `4px solid var(--crit-${finding.severity})` }}>
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                            <div>
                              <h5 style={{ color: '#fff', fontSize: '0.85rem', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Description</h5>
                              {/* Stored raw, rendered as text safely in React (escapes potential stored XSS scripts) */}
                              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>
                                {finding.description || 'No description provided.'}
                              </p>
                            </div>
                            <div>
                              <h5 style={{ color: '#fff', fontSize: '0.85rem', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Remediation Plan</h5>
                              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', fontStyle: 'italic' }}>
                                {finding.remediation || 'No remediation guidelines mapped.'}
                              </p>
                              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '1rem' }}>
                                Discovered by operator: <strong>{finding.discovered_by}</strong> | Timestamp: {new Date(finding.created_at).toLocaleString()}
                              </p>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
              {findings.length === 0 && (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>
                    No vulnerability findings discovered.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Finding Modal */}
      {showAddModal && (
        <div className="modal-overlay">
          <div className="glass-card modal-content" style={{ maxWidth: '650px' }}>
            <div className="modal-header">
              <h3>Log Security Vulnerability</h3>
              <button 
                onClick={() => setShowAddModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleCreateFinding}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label>Finding Title</label>
                  <input 
                    type="text" 
                    className="form-input" 
                    value={title} 
                    onChange={e => setTitle(e.target.value)} 
                    placeholder="e.g., Insecure JWT Signature Verification"
                    required 
                  />
                </div>

                <div className="form-group">
                  <label>Affected Asset</label>
                  <select 
                    className="form-input" 
                    value={assetId} 
                    onChange={e => setAssetId(e.target.value)}
                    required
                  >
                    {assets.map(a => (
                      <option key={a.id} value={a.id}>{a.name} ({a.type})</option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label>Severity Level</label>
                  <select className="form-input" value={severity} onChange={e => setSeverity(e.target.value)}>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Compliance Control Alignment</label>
                  <select 
                    className="form-input" 
                    value={controlId} 
                    onChange={e => setControlId(e.target.value)}
                  >
                    <option value="">None (General Weakness)</option>
                    {controls.map(c => (
                      <option key={c.id} value={c.id}>{c.frameworkName} - {c.section_code} ({c.title})</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Description & Proof of Concept</label>
                <textarea 
                  className="form-input" 
                  rows="4" 
                  value={description} 
                  onChange={e => setDescription(e.target.value)} 
                  placeholder="Provide details on the vulnerability, input vectors, or proof-of-concept evidence..."
                  required
                />
              </div>

              <div className="form-group">
                <label>Remediation & Mitigation Guidance</label>
                <textarea 
                  className="form-input" 
                  rows="3" 
                  value={remediation} 
                  onChange={e => setRemediation(e.target.value)} 
                  placeholder="Provide actionable code changes or configuration hardening guides..."
                  required
                />
              </div>

              <div className="form-group">
                <label>Discovered By (Optional)</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={discoveredBy} 
                  onChange={e => setDiscoveredBy(e.target.value)} 
                  placeholder={user.username}
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Submitting...' : 'Submit Finding'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
