import React, { useState, useEffect } from 'react';
import { 
  Boxes, 
  ShieldCheck, 
  AlertTriangle, 
  FileSpreadsheet, 
  History,
  Lock,
  Loader2
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip as ChartTooltip,
  Legend
} from 'recharts';

export default function Dashboard({ apiCall }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiCall('/api/dashboard/stats')
      .then(res => {
        if (!res.ok) throw new Error('Failed to load dashboard metrics');
        return res.json();
      })
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const triggerExport = (format) => {
    // For HTML, we can open in a new window or trigger download
    if (format === 'html') {
      window.open('/api/reports/html', '_blank');
    } else {
      window.open('/api/reports/json', '_blank');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
        <Loader2 className="logo-icon" style={{ animation: 'spin 1s linear infinite' }} size={32} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', borderLeft: '4px solid var(--error)' }}>
        <p style={{ color: '#ef4444' }}>{error}</p>
      </div>
    );
  }

  // Formatting finding severity data for Recharts Pie
  const severityData = [
    { name: 'Critical', value: stats.findings_by_severity.critical, color: '#ef4444' },
    { name: 'High', value: stats.findings_by_severity.high, color: '#f97316' },
    { name: 'Medium', value: stats.findings_by_severity.medium, color: '#f59e0b' },
    { name: 'Low', value: stats.findings_by_severity.low, color: '#3b82f6' }
  ].filter(item => item.value > 0);

  // Formatting control status distribution for Recharts Bar
  const controlData = [
    { name: 'Compliant', count: stats.control_status_distribution.compliant, color: '#10b981' },
    { name: 'Implementing', count: stats.control_status_distribution.implementing, color: '#f59e0b' },
    { name: 'Not Started', count: stats.control_status_distribution.not_started, color: '#64748b' },
    { name: 'Non Compliant', count: stats.control_status_distribution.non_compliant, color: '#ef4444' }
  ];

  return (
    <div>
      {/* Quick Export Panel */}
      <div className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.25rem 2rem', marginBottom: '2rem' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '0.25rem' }}>Compliance Readiness Report</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Download comprehensive secure audit evidence package.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-secondary" onClick={() => triggerExport('json')}>
            Export JSON
          </button>
          <button className="btn btn-primary" onClick={() => triggerExport('html')}>
            <FileSpreadsheet size={16} />
            Generate HTML Report
          </button>
        </div>
      </div>

      {/* Stats Cards Row */}
      <div className="grid-stats">
        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ color: 'var(--info)' }}>
            <Boxes size={24} />
          </div>
          <div className="stat-info">
            <div className="stat-val">{stats.total_assets}</div>
            <div className="stat-lbl">Assessed Assets</div>
          </div>
        </div>

        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ color: 'var(--success)' }}>
            <ShieldCheck size={24} />
          </div>
          <div className="stat-info">
            <div className="stat-val">{stats.compliance_score}%</div>
            <div className="stat-lbl">Compliance Score</div>
          </div>
        </div>

        <div className="glass-card stat-card">
          <div className="stat-icon" style={{ color: 'var(--error)' }}>
            <AlertTriangle size={24} />
          </div>
          <div className="stat-info">
            <div className="stat-val">{stats.open_findings_count}</div>
            <div className="stat-lbl">Open Vulnerabilities</div>
          </div>
        </div>
      </div>

      {/* Charts Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Severity Pie Chart */}
        <div className="glass-card" style={{ minHeight: '350px' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1.5rem' }}>Active Vulnerabilities by Severity</h3>
          {severityData.length > 0 ? (
            <div style={{ width: '100%', height: 240 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <ChartTooltip 
                    contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', borderRadius: '6px' }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ height: '240px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
              No open vulnerabilities logged
            </div>
          )}
        </div>

        {/* Control Status Bar Chart */}
        <div className="glass-card" style={{ minHeight: '350px' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1.5rem' }}>Security Controls Status</h3>
          <div style={{ width: '100%', height: 240 }}>
            <ResponsiveContainer>
              <BarChart data={controlData}>
                <XAxis dataKey="name" stroke="var(--text-secondary)" fontSize={11} tickLine={false} />
                <YAxis stroke="var(--text-secondary)" fontSize={11} tickLine={false} />
                <ChartTooltip 
                  contentStyle={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', borderRadius: '6px' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {controlData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Audit Log Feed */}
      <div className="glass-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <History size={20} style={{ color: 'var(--primary)' }} />
          <h3 style={{ fontSize: '1.1rem' }}>Tamper-Evident Security Log Trail</h3>
        </div>

        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Operator Action</th>
                <th>Details</th>
                <th>Log Verification Hash</th>
              </tr>
            </thead>
            <tbody>
              {stats.recent_activities && stats.recent_activities.length > 0 ? (
                stats.recent_activities.map((log) => (
                  <tr key={log.id}>
                    <td style={{ fontSize: '0.8rem', whiteSpace: 'nowrap', color: 'var(--text-muted)' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td>
                      <strong style={{ fontSize: '0.9rem', color: '#fff' }}>{log.action}</strong>
                    </td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      {log.details}
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--success)', fontSize: '0.75rem', fontFamily: 'monospace' }}>
                        <Lock size={12} style={{ flexShrink: 0 }} />
                        <span title={`Hash chain node validation code: ${log.entry_hash}`}>
                          {log.entry_hash.substring(0, 16)}...
                        </span>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                    No audit logs available
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
