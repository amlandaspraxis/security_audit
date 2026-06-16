from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str
    must_reset_password: bool = False

class TokenData(BaseModel):
    username: Optional[str] = None

# --- User Schemas ---
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    role: str = Field(default="developer", pattern="^(admin|auditor|developer)$")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserPasswordReset(BaseModel):
    current_password: str
    new_password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern="^(admin|auditor|developer)$")
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    must_reset_password: bool

    class Config:
        from_attributes = True

# --- Asset Schemas ---
class AssetBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    type: str = Field(..., pattern="^(web_app|api|server|database)$")
    critical_level: str = Field(..., pattern="^(low|medium|high|critical)$")
    description: Optional[str] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    type: Optional[str] = Field(None, pattern="^(web_app|api|server|database)$")
    critical_level: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    description: Optional[str] = None

class AssetResponse(AssetBase):
    id: int
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True

# --- Control Schemas ---
class ControlBase(BaseModel):
    section_code: str
    title: str
    description: Optional[str] = None
    state: str = Field(default="not_started", pattern="^(not_started|implementing|compliant|non_compliant)$")

class ControlUpdate(BaseModel):
    state: str = Field(..., pattern="^(not_started|implementing|compliant|non_compliant)$")

class ControlResponse(ControlBase):
    id: int
    framework_id: int

    class Config:
        from_attributes = True

# --- Framework Schemas ---
class FrameworkBase(BaseModel):
    name: str
    version: str
    description: Optional[str] = None

class FrameworkResponse(FrameworkBase):
    id: int
    controls: List[ControlResponse] = []

    class Config:
        from_attributes = True

# --- Finding Schemas ---
class FindingBase(BaseModel):
    asset_id: int
    control_id: Optional[int] = None
    title: str = Field(..., min_length=5, max_length=150)
    description: Optional[str] = None
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    status: str = Field(default="open", pattern="^(open|in_progress|resolved|accepted_risk)$")
    remediation: Optional[str] = None
    discovered_by: Optional[str] = None

class FindingCreate(FindingBase):
    pass

class FindingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=150)
    description: Optional[str] = None
    severity: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    status: Optional[str] = Field(None, pattern="^(open|in_progress|resolved|accepted_risk)$")
    remediation: Optional[str] = None
    discovered_by: Optional[str] = None
    control_id: Optional[int] = None

class FindingResponse(FindingBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Audit Log Schemas ---
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    timestamp: datetime
    details: Optional[str] = None
    entry_hash: str
    prev_hash: Optional[str] = None

    class Config:
        from_attributes = True

# --- Dashboard Stats Schemas ---
class DashboardStats(BaseModel):
    total_assets: int
    compliance_score: float  # Percentage of controls that are compliant
    open_findings_count: int
    findings_by_severity: dict
    control_status_distribution: dict
    recent_activities: List[AuditLogResponse]
