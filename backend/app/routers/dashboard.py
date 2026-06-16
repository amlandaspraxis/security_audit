from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import get_current_active_user
from app.models.models import User, Asset, Finding, Control, AuditLog
from app.schemas.schemas import DashboardStats
from typing import Dict

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Aggregate stats for the compliance platform landing dashboard."""
    # Assets count
    total_assets = db.query(Asset).count()

    # Findings count
    open_findings = db.query(Finding).filter(Finding.status.in_(["open", "in_progress"])).all()
    open_findings_count = len(open_findings)

    # Findings by severity
    findings_by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in open_findings:
        sev = f.severity.lower()
        if sev in findings_by_severity:
            findings_by_severity[sev] += 1

    # Control compliance stats
    controls = db.query(Control).all()
    total_controls = len(controls)
    compliant_count = sum(1 for c in controls if c.state == "compliant")
    
    compliance_score = (compliant_count / total_controls * 100) if total_controls > 0 else 0.0

    control_status_distribution = {"not_started": 0, "implementing": 0, "compliant": 0, "non_compliant": 0}
    for c in controls:
        state = c.state.lower()
        if state in control_status_distribution:
            control_status_distribution[state] += 1

    # Recent activity logs (limit to 10)
    recent_logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(10).all()

    return {
        "total_assets": total_assets,
        "compliance_score": round(compliance_score, 1),
        "open_findings_count": open_findings_count,
        "findings_by_severity": findings_by_severity,
        "control_status_distribution": control_status_distribution,
        "recent_activities": recent_logs
    }
