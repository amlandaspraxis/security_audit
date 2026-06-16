from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.models import AuditLog

def log_activity(db: Session, user_id: Optional[int], action: str, details: str) -> AuditLog:
    """Log an activity with hash-chaining to make the log tamper-evident."""
    # Find the most recent log to get its hash
    last_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last_log.entry_hash if last_log else None

    timestamp = datetime.now(timezone.utc)
    
    # Calculate the hash for this new entry
    entry_hash = AuditLog.calculate_hash(
        prev_hash=prev_hash,
        user_id=user_id,
        action=action,
        timestamp=timestamp,
        details=details
    )

    db_log = AuditLog(
        user_id=user_id,
        action=action,
        timestamp=timestamp,
        details=details,
        prev_hash=prev_hash,
        entry_hash=entry_hash
    )
    
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log
