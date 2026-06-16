import html
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import get_current_active_user
from app.models.models import User, Asset, Finding, Control, Framework
from typing import Dict, Any

router = APIRouter(prefix="/api/reports", tags=["reports"])

def build_report_data(db: Session) -> Dict[str, Any]:
    """Compile audit and compliance data for report exports."""
    assets = db.query(Asset).all()
    findings = db.query(Finding).all()
    controls = db.query(Control).all()
    frameworks = db.query(Framework).all()

    # Calculate compliance score
    compliant_count = sum(1 for c in controls if c.state == "compliant")
    total_controls = len(controls)
    compliance_score = (compliant_count / total_controls * 100) if total_controls > 0 else 0.0

    # Count findings by severity
    findings_by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        severity = f.severity.lower()
        if severity in findings_by_severity:
            findings_by_severity[severity] += 1

    # Count findings by status
    findings_by_status = {"open": 0, "in_progress": 0, "resolved": 0, "accepted_risk": 0}
    for f in findings:
        status = f.status.lower()
        if status in findings_by_status:
            findings_by_status[status] += 1

    return {
        "compliance_score": round(compliance_score, 1),
        "total_assets": len(assets),
        "total_findings": len(findings),
        "total_controls": total_controls,
        "findings_by_severity": findings_by_severity,
        "findings_by_status": findings_by_status,
        "assets": [
            {
                "id": a.id,
                "name": a.name,
                "type": a.type,
                "critical_level": a.critical_level,
                "description": a.description or ""
            }
            for a in assets
        ],
        "findings": [
            {
                "id": f.id,
                "title": f.title,
                "severity": f.severity,
                "status": f.status,
                "description": f.description or "",
                "remediation": f.remediation or "",
                "discovered_by": f.discovered_by or "",
                "asset_name": db.query(Asset.name).filter(Asset.id == f.asset_id).scalar() or "Unknown Asset"
            }
            for f in findings
        ],
        "frameworks": [
            {
                "name": fw.name,
                "version": fw.version,
                "description": fw.description or "",
                "compliant_controls": sum(1 for c in fw.controls if c.state == "compliant"),
                "total_controls": len(fw.controls)
            }
            for fw in frameworks
        ]
    }

@router.get("/json")
def get_report_json(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Retrieve raw compliance report data in JSON format."""
    return build_report_data(db)

@router.get("/html", response_class=HTMLResponse)
def get_report_html(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Generate and return a beautifully styled, self-contained HTML report with auto-escaped inputs to prevent XSS."""
    data = build_report_data(db)

    # Safe escaping helper
    def esc(text: Any) -> str:
        return html.escape(str(text)) if text is not None else ""

    # Build Framework Cards HTML
    frameworks_html = ""
    for fw in data["frameworks"]:
        score = (fw["compliant_controls"] / fw["total_controls"] * 100) if fw["total_controls"] > 0 else 0
        frameworks_html += f"""
        <div class="card">
            <h3>{esc(fw["name"])} (v{esc(fw["version"])})</h3>
            <p class="muted">{esc(fw["description"])}</p>
            <div class="metric">
                <span class="value">{fw["compliant_controls"]} / {fw["total_controls"]}</span> Controls Compliant ({round(score, 1)}%)
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: {score}%"></div>
            </div>
        </div>
        """

    # Build Assets HTML
    assets_html = ""
    for a in data["assets"]:
        assets_html += f"""
        <tr>
            <td><strong>{esc(a["name"])}</strong></td>
            <td><span class="badge badge-type">{esc(a["type"])}</span></td>
            <td><span class="badge badge-crit-{a["critical_level"]}">{esc(a["critical_level"].upper())}</span></td>
            <td>{esc(a["description"])}</td>
        </tr>
        """
    if not data["assets"]:
        assets_html = "<tr><td colspan='4' class='text-center muted'>No assets in inventory.</td></tr>"

    # Build Findings HTML
    findings_html = ""
    for f in data["findings"]:
        findings_html += f"""
        <div class="finding-item finding-crit-{f["severity"].lower()}">
            <div class="finding-header">
                <strong>{esc(f["title"])}</strong>
                <div>
                    <span class="badge badge-crit-{f["severity"].lower()}">{esc(f["severity"].upper())}</span>
                    <span class="badge badge-status">{esc(f["status"].replace('_', ' ').title())}</span>
                </div>
            </div>
            <p><strong>Asset:</strong> {esc(f["asset_name"])}</p>
            <p><strong>Description:</strong> {esc(f["description"])}</p>
            <p><strong>Remediation:</strong> <em>{esc(f["remediation"])}</em></p>
            <p class="muted small">Discovered by: {esc(f["discovered_by"])}</p>
        </div>
        """
    if not data["findings"]:
        findings_html = "<p class='muted text-center'>No active security findings logged.</p>"

    # Full HTML report document
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Compliance Audit Report</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #6366f1;
            --border: #334155;
            --crit-critical: #ef4444;
            --crit-high: #f97316;
            --crit-medium: #eab308;
            --crit-low: #3b82f6;
            --status-bg: #475569;
        }}
        body {{
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 2rem;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        header {{
            border-bottom: 2px solid var(--border);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
        }}
        h1 {{ margin: 0 0 0.5rem 0; font-size: 2.2rem; color: #fff; }}
        h2 {{ border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin-top: 2rem; font-size: 1.5rem; color: #e2e8f0; }}
        .muted {{ color: var(--text-muted); }}
        .small {{ font-size: 0.85rem; }}
        .text-center {{ text-align: center; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
        }}
        .card h3 {{ margin: 0 0 0.5rem 0; font-size: 1.2rem; }}
        .metric {{ font-size: 1rem; margin-top: 1rem; }}
        .metric .value {{ font-size: 1.8rem; font-weight: bold; color: #fff; display: block; }}
        .progress-bar-bg {{
            background-color: var(--border);
            height: 8px;
            border-radius: 4px;
            margin-top: 0.5rem;
            overflow: hidden;
        }}
        .progress-bar-fill {{
            background-color: var(--primary);
            height: 100%;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
            background-color: var(--card-bg);
            border-radius: 8px;
            overflow: hidden;
        }}
        th, td {{
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            background-color: #111827;
            font-weight: 600;
            color: var(--text-muted);
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .badge-type {{ background-color: var(--status-bg); color: #fff; }}
        .badge-status {{ background-color: #0f766e; color: #fff; }}
        .badge-crit-critical {{ background-color: var(--crit-critical); color: #fff; }}
        .badge-crit-high {{ background-color: var(--crit-high); color: #fff; }}
        .badge-crit-medium {{ background-color: var(--crit-medium); color: #000; }}
        .badge-crit-low {{ background-color: var(--crit-low); color: #fff; }}
        
        .finding-item {{
            background-color: var(--card-bg);
            border-left: 5px solid var(--border);
            border-radius: 0 8px 8px 0;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid var(--border);
            border-left-width: 6px;
        }}
        .finding-crit-critical {{ border-left-color: var(--crit-critical); }}
        .finding-crit-high {{ border-left-color: var(--crit-high); }}
        .finding-crit-medium {{ border-left-color: var(--crit-medium); }}
        .finding-crit-low {{ border-left-color: var(--crit-low); }}
        
        .finding-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}
        .finding-header strong {{ font-size: 1.2rem; color: #fff; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Security Audit & Compliance Report</h1>
            <p class="muted">Generated on {esc(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))} | Generated by: {esc(current_user.username)}</p>
        </header>

        <section class="grid">
            <div class="card">
                <h3>Overall Compliance</h3>
                <div class="metric">
                    <span class="value">{data["compliance_score"]}%</span>
                    Framework requirement status
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: {data["compliance_score"]}%"></div>
                </div>
            </div>
            <div class="card">
                <h3>Asset Coverage</h3>
                <div class="metric">
                    <span class="value">{data["total_assets"]}</span>
                    Assets registered under audit
                </div>
            </div>
            <div class="card">
                <h3>Open Findings</h3>
                <div class="metric">
                    <span class="value">{data["total_findings"]}</span>
                    Active security vulnerabilities
                </div>
            </div>
        </section>

        <h2>Compliance Framework Status</h2>
        <section class="grid">
            {frameworks_html}
        </section>

        <h2>Asset Inventory</h2>
        <table>
            <thead>
                <tr>
                    <th>Asset Name</th>
                    <th>Type</th>
                    <th>Criticality</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                {assets_html}
            </tbody>
        </table>

        <h2>Discovered Vulnerabilities (Findings)</h2>
        <section>
            {findings_html}
        </section>
    </div>
</body>
</html>
"""
    return html_content
