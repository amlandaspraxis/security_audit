from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import get_current_active_user, require_auditor_or_admin
from app.models.models import User, Asset
from app.schemas.schemas import AssetResponse, AssetCreate, AssetUpdate
from app.core.logging import log_activity
from typing import List

router = APIRouter(prefix="/api/assets", tags=["assets"])

@router.get("", response_model=List[AssetResponse])
def get_assets(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Retrieve all digital assets. Accessible to all authenticated active users."""
    return db.query(Asset).all()

@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Retrieve a single digital asset by ID."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(asset_in: AssetCreate, current_user: User = Depends(require_auditor_or_admin), db: Session = Depends(get_db)):
    """Register a new digital asset. Gated to auditor or admin roles."""
    asset = Asset(
        name=asset_in.name,
        type=asset_in.type,
        critical_level=asset_in.critical_level,
        description=asset_in.description,
        owner_id=current_user.id
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    log_activity(db, user_id=current_user.id, action="ASSET_CREATED", details=f"Asset '{asset.name}' (ID: {asset.id}) created by user {current_user.username}")
    return asset

@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(asset_id: int, asset_in: AssetUpdate, current_user: User = Depends(require_auditor_or_admin), db: Session = Depends(get_db)):
    """Update asset specifications. Gated to auditor or admin roles."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    update_data = asset_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(asset, key, value)
        
    db.commit()
    db.refresh(asset)
    
    log_activity(db, user_id=current_user.id, action="ASSET_UPDATED", details=f"Asset '{asset.name}' (ID: {asset.id}) updated by user {current_user.username}")
    return asset

@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(asset_id: int, current_user: User = Depends(require_auditor_or_admin), db: Session = Depends(get_db)):
    """Delete an asset from inventory. Gated to auditor or admin roles."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    asset_name = asset.name
    db.delete(asset)
    db.commit()
    
    log_activity(db, user_id=current_user.id, action="ASSET_DELETED", details=f"Asset '{asset_name}' (ID: {asset_id}) deleted by user {current_user.username}")
    return None
