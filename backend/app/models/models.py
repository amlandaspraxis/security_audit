import hashlib
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="developer", nullable=False) # admin, auditor, developer
    is_active = Column(Boolean, default=True, nullable=False)
    must_reset_password = Column(Boolean, default=False, nullable=False)

    assets = relationship("Asset", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False) # web_app, api, server, database
    critical_level = Column(String(20), nullable=False) # low, medium, high, critical
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", back_populates="assets")
    findings = relationship("Finding", back_populates="asset", cascade="all, delete-orphan")

class Framework(Base):
    __tablename__ = "frameworks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False) # SOC 2, ISO 27001, OWASP ASVS
    version = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)

    controls = relationship("Control", back_populates="framework", cascade="all, delete-orphan")

class Control(Base):
    __tablename__ = "controls"

    id = Column(Integer, primary_key=True, index=True)
    framework_id = Column(Integer, ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False)
    section_code = Column(String(50), nullable=False) # e.g., CC6.1, A.12.1.1
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    state = Column(String(30), default="not_started", nullable=False) # not_started, implementing, compliant, non_compliant

    framework = relationship("Framework", back_populates="controls")
    findings = relationship("Finding", back_populates="control")

class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    control_id = Column(Integer, ForeignKey("controls.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False) # low, medium, high, critical
    status = Column(String(20), default="open", nullable=False) # open, in_progress, resolved, accepted_risk
    remediation = Column(Text, nullable=True)
    discovered_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    asset = relationship("Asset", back_populates="findings")
    control = relationship("Control", back_populates="findings")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    details = Column(Text, nullable=True)
    prev_hash = Column(String(64), nullable=True)
    entry_hash = Column(String(64), nullable=False)

    user = relationship("User", back_populates="audit_logs")

    @classmethod
    def calculate_hash(cls, prev_hash: str, user_id: int, action: str, timestamp: datetime, details: str) -> str:
        """Compute SHA256 chain hash for tamper-evident logs."""
        hash_input = f"{prev_hash or ''}|{user_id or 0}|{action}|{timestamp.isoformat()}|{details or ''}"
        return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()
