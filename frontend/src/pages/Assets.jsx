import React, { useState, useEffect } from 'react';
import { Plus, Trash2, ShieldAlert, Monitor, Server, Database, Code, Loader2 } from 'lucide-react';

export default function Assets({ user, apiCall }) {
  const [assets, setAssets] = useState([]);
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [name, setName] = useState('');
  const [type, setType] = useState('web_app');
  const [criticalLevel, setCriticalLevel] = useState('medium');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadData = async () => {
    try {
      const assetsRes = await apiCall('/api/assets');
      const assetsData = await assetsRes.json();
      
      const findingsRes = await apiCall('/api/findings');
      const findingsData = await findingsRes.json();

      setAssets(assetsData);
      setFindings(findingsData);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAddAsset = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const res = await apiCall('/api/assets', {
        method: 'POST',
        body: JSON.stringify({ name, type, critical_level: criticalLevel, description })
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to register asset');
      }

      setName('');
      setDescription('');
      setShowAddModal(false);
      loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteAsset = async (assetId) => {
    if (!window.confirm('Are you sure you want to remove this asset? This will also remove any linked vulnerabilities.')) {
      return;
    }
    setError(null);
    try {
      const res = await apiCall(`/api/assets/${assetId}`, {
        method: 'DELETE'
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to delete asset');
      }

      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const getAssetIcon = (assetType) => {
    switch (assetType) {
      case 'web_app': return <Monitor size={18} />;
      case 'server': return <Server size={18} />;
      case 'database': return <Database size={18} />;
      case 'api': return <Code size={18} />;
      default: return <Monitor size={18} />;
    }
  };

  // Helper to count findings linked to this asset
  const getAssetFindingsCount = (assetId) => {
    return findings.filter(f => f.asset_id === assetId && f.status !== 'resolved').length;
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

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h2 style={{ fontSize: '1.4rem' }}>Assessed Systems Directory</h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Inventory of all targets monitored for security audits.</p>
        </div>
        {isMutationAllowed && (
          <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
            <Plus size={16} />
            <span>Register Asset</span>
          </button>
        )}
      </div>

      {/* Assets Grid List */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.5rem' }}>
        {assets.map((asset) => {
          const vulnCount = getAssetFindingsCount(asset.id);
          return (
            <div key={asset.id} className="glass-card" style={{ display: 'flex', flexDirection: 'column', minHeight: '200px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div className="stat-icon" style={{ width: '40px', height: '40px', borderRadius: '8px', color: 'var(--primary)' }}>
                    {getAssetIcon(asset.type)}
                  </div>
                  <div>
                    <h4 style={{ fontSize: '1.05rem', color: '#fff' }}>{asset.name}</h4>
                    <span className="badge badge-low" style={{ fontSize: '0.65rem', marginTop: '0.25rem' }}>{asset.type.replace('_', ' ')}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <span className={`badge badge-${asset.critical_level}`}>{asset.critical_level}</span>
                  {isMutationAllowed && (
                    <button 
                      onClick={() => handleDeleteAsset(asset.id)} 
                      style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}
                      title="Remove asset"
                    >
                      <Trash2 size={16} style={{ hover: { color: 'var(--error)' } }} />
                    </button>
                  )}
                </div>
              </div>

              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', flex: 1, marginBottom: '1.5rem' }}>
                {asset.description || 'No description provided.'}
              </p>

              <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Security Findings</span>
                <span className={`badge ${vulnCount > 0 ? 'badge-critical' : 'badge-compliant'}`}>
                  {vulnCount} Active {vulnCount === 1 ? 'Vulnerability' : 'Vulnerabilities'}
                </span>
              </div>
            </div>
          );
        })}
        {assets.length === 0 && (
          <div style={{ gridColumn: '1 / -1', padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
            No assets registered yet.
          </div>
        )}
      </div>

      {/* Add Asset Modal */}
      {showAddModal && (
        <div className="modal-overlay">
          <div className="glass-card modal-content">
            <div className="modal-header">
              <h3>Register Digital Asset</h3>
              <button 
                onClick={() => setShowAddModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', fontSize: '1.2rem' }}
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleAddAsset}>
              <div className="form-group">
                <label>Asset Name</label>
                <input 
                  type="text" 
                  className="form-input" 
                  value={name} 
                  onChange={e => setName(e.target.value)} 
                  placeholder="e.g., Core Billing API"
                  required 
                />
              </div>

              <div className="form-group">
                <label>Asset Type</label>
                <select className="form-input" value={type} onChange={e => setType(e.target.value)}>
                  <option value="web_app">Web Application</option>
                  <option value="api">REST / GraphQL API</option>
                  <option value="server">Linux / Host Server</option>
                  <option value="database">Database System</option>
                </select>
              </div>

              <div className="form-group">
                <label>Business Criticality</label>
                <select className="form-input" value={criticalLevel} onChange={e => setCriticalLevel(e.target.value)}>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea 
                  className="form-input" 
                  rows="3" 
                  value={description} 
                  onChange={e => setDescription(e.target.value)} 
                  placeholder="Describe context, components, and primary owners..."
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Registering...' : 'Register Asset'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
