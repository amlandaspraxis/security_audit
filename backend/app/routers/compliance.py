from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import get_current_active_user, require_auditor_or_admin
from app.models.models import User, Framework, Control
from app.schemas.schemas import FrameworkResponse, ControlResponse, ControlUpdate
from app.core.logging import log_activity
from typing import List

router = APIRouter(prefix="/api/compliance", tags=["compliance"])

@router.get("/frameworks", response_model=List[FrameworkResponse])
def get_frameworks(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """List all registered compliance frameworks and their controls."""
    return db.query(Framework).all()

@router.get("/frameworks/{framework_id}", response_model=FrameworkResponse)
def get_framework(framework_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Retrieve details for a single compliance framework."""
    framework = db.query(Framework).filter(Framework.id == framework_id).first()
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")
    return framework

@router.put("/controls/{control_id}", response_model=ControlResponse)
def update_control_state(control_id: int, control_in: ControlUpdate, current_user: User = Depends(require_auditor_or_admin), db: Session = Depends(get_db)):
    """Update implementation state for a specific security control. Gated to auditor/admin roles."""
    control = db.query(Control).filter(Control.id == control_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
        
    old_state = control.state
    control.state = control_in.state
    db.commit()
    db.refresh(control)
    
    log_activity(
        db, 
        user_id=current_user.id, 
        action="CONTROL_STATE_UPDATED", 
        details=f"Control '{control.section_code}' updated from '{old_state}' to '{control.state}' by {current_user.username}"
    )
    return control
