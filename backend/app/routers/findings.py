from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import get_current_active_user, require_auditor_or_admin
from app.models.models import User, Finding, Asset, Control
from app.schemas.schemas import FindingResponse, FindingCreate, FindingUpdate
from app.core.logging import log_activity
from typing import List, Optional

router = APIRouter(prefix="/api/findings", tags=["findings"])

@router.get("", response_model=List[FindingResponse])
def get_findings(
    asset_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve all findings, optionally filtered by asset_id or status. Accessible to all active users."""
    query = db.query(Finding)
    if asset_id is not None:
        query = query.filter(Finding.asset_id == asset_id)
    if status is not None:
        query = query.filter(Finding.status == status)
    return query.all()

@router.get("/{finding_id}", response_model=FindingResponse)
def get_finding(finding_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Retrieve a single finding by ID."""
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding

@router.post("", response_model=FindingResponse, status_code=status.HTTP_201_CREATED)
def create_finding(finding_in: FindingCreate, current_user: User = Depends(require_auditor_or_admin), db: Session = Depends(get_db)):
    """Create a new security finding. Gated to auditor or admin roles."""
    # Verify asset exists
    asset = db.query(Asset).filter(Asset.id == finding_in.asset_id).first()
    if not asset:
        raise HTTPException(status_code=400, detail="Associated asset does not exist")
        
    # Verify control exists if supplied
    if finding_in.control_id is not None:
        control = db.query(Control).filter(Control.id == finding_in.control_id).first()
        if not control:
            raise HTTPException(status_code=400, detail="Associated control does not exist")
            
    finding = Finding(
        asset_id=finding_in.asset_id,
        control_id=finding_in.control_id,
        title=finding_in.title,
        description=finding_in.description, # Stored as-is, escaped at render time
        severity=finding_in.severity,
        status=finding_in.status,
        remediation=finding_in.remediation, # Stored as-is, escaped at render time
        discovered_by=finding_in.discovered_by or current_user.username
    )
    db.add(finding)
    db.commit()
    db.refresh(finding)
    
    log_activity(
        db, 
        user_id=current_user.id, 
        action="FINDING_CREATED", 
        details=f"Finding '{finding.title}' (ID: {finding.id}, Severity: {finding.severity}) created by {current_user.username}"
    )
    return finding

@router.put("/{finding_id}", response_model=FindingResponse)
def update_finding(finding_id: int, finding_in: FindingUpdate, current_user: User = Depends(require_auditor_or_admin), db: Session = Depends(get_db)):
    """Update a finding's status, severity, or details. Gated to auditor or admin roles."""
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
        
    # Verify control exists if updating it
    if finding_in.control_id is not None:
        control = db.query(Control).filter(Control.id == finding_in.control_id).first()
        if not control:
            raise HTTPException(status_code=400, detail="Associated control does not exist")

    update_data = finding_in.model_dump(exclude_unset=True)
    old_status = finding.status
    old_severity = finding.severity
    
    for key, value in update_data.items():
        setattr(finding, key, value)
        
    db.commit()
    db.refresh(finding)
    
    log_activity(
        db, 
        user_id=current_user.id, 
        action="FINDING_UPDATED", 
        details=f"Finding '{finding.title}' (ID: {finding_id}) updated by {current_user.username}. Status: {old_status} -> {finding.status}, Severity: {old_severity} -> {finding.severity}"
    )
    return finding

@router.delete("/{finding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_finding(finding_id: int, current_user: User = Depends(require_auditor_or_admin), db: Session = Depends(get_db)):
    """Delete a finding from the system. Gated to auditor or admin roles (developers are rejected)."""
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
        
    finding_title = finding.title
    db.delete(finding)
    db.commit()
    
    log_activity(
        db, 
        user_id=current_user.id, 
        action="FINDING_DELETED", 
        details=f"Finding '{finding_title}' (ID: {finding_id}) deleted by {current_user.username}"
    )
    return None
