import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.models import User, Asset, Control, Framework, AuditLog

from app.core.limiter import limiter
limiter.enabled = False

# Configure Test Database
SQLALCHEMY_DATABASE_URL = "sqlite://" # In-memory DB
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override get_db dependency in FastAPI app
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    """Create a clean database schema before each test run."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Seed compliance frameworks
    fw = Framework(name="SOC 2", version="2017", description="SOC2 Framework")
    db.add(fw)
    db.commit()
    db.refresh(fw)
    
    ctrl = Control(framework_id=fw.id, section_code="CC6.1", title="Logical Access", state="not_started")
    db.add(ctrl)
    
    # Create test users with distinct roles
    db.add(User(
        username="test_admin",
        email="admin@test.local",
        hashed_password=hash_password("AdminPass123!"),
        role="admin",
        is_active=True,
        must_reset_password=False
    ))
    db.add(User(
        username="test_auditor",
        email="auditor@test.local",
        hashed_password=hash_password("AuditorPass123!"),
        role="auditor",
        is_active=True,
        must_reset_password=False
    ))
    db.add(User(
        username="test_dev",
        email="dev@test.local",
        hashed_password=hash_password("DevPass123!"),
        role="developer",
        is_active=True,
        must_reset_password=False
    ))
    db.commit()
    db.close()
    
    yield
    Base.metadata.drop_all(bind=engine)

def get_auth_token(username, password):
    """Utility helper to request a Bearer token."""
    response = client.post(
        "/api/auth/login",
        data={"username": username, "password": password}
    )
    return response.json()["access_token"]

# --- AUTHENTICATION TESTS ---
def test_login_success():
    response = client.post(
        "/api/auth/login",
        data={"username": "test_admin", "password": "AdminPass123!"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_credentials():
    response = client.post(
        "/api/auth/login",
        data={"username": "test_admin", "password": "WrongPassword!"}
    )
    assert response.status_code == 401

# --- ROLE-BASED ACCESS CONTROL TESTS ---
def test_developer_asset_creation_denied():
    token = get_auth_token("test_dev", "DevPass123!")
    response = client.post(
        "/api/assets",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Protected DB", "type": "database", "critical_level": "high", "description": "Backend database"}
    )
    assert response.status_code == 403
    assert "Required roles" in response.json()["detail"]

def test_auditor_asset_creation_allowed():
    token = get_auth_token("test_auditor", "AuditorPass123!")
    response = client.post(
        "/api/assets",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Protected DB", "type": "database", "critical_level": "high", "description": "Backend database"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Protected DB"

def test_developer_control_modification_denied():
    # Setup - find control ID
    db = TestingSessionLocal()
    ctrl = db.query(Control).first()
    control_id = ctrl.id
    db.close()
    
    token = get_auth_token("test_dev", "DevPass123!")
    response = client.put(
        f"/api/compliance/controls/{control_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"state": "compliant"}
    )
    assert response.status_code == 403

def test_auditor_control_modification_allowed():
    db = TestingSessionLocal()
    ctrl = db.query(Control).first()
    control_id = ctrl.id
    db.close()
    
    token = get_auth_token("test_auditor", "AuditorPass123!")
    response = client.put(
        f"/api/compliance/controls/{control_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"state": "compliant"}
    )
    assert response.status_code == 200
    assert response.json()["state"] == "compliant"

# --- TAMPER-EVIDENT AUDIT TRAIL TESTS ---
def test_audit_log_immutable():
    # Attempt to post a mock request to modify or delete logs (not exposed in routers)
    # Testing path absence
    token = get_auth_token("test_admin", "AdminPass123!")
    
    # Try PUT request
    response_put = client.put(
        "/api/audit_logs/1",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "MODIFIED"}
    )
    assert response_put.status_code == 404 # Endpoint does not exist

    # Try DELETE request
    response_del = client.delete(
        "/api/audit_logs/1",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response_del.status_code == 404 # Endpoint does not exist

def test_audit_log_hash_chain():
    db = TestingSessionLocal()
    # Trigger acts to write logs
    token = get_auth_token("test_admin", "AdminPass123!")
    
    # Fetch logs from DB directly
    logs = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    assert len(logs) > 0
    
    # Check chaining validation
    for i in range(1, len(logs)):
        assert logs[i].prev_hash == logs[i-1].entry_hash
        
        # Recalculate hash to verify integrity
        calculated = AuditLog.calculate_hash(
            prev_hash=logs[i].prev_hash,
            user_id=logs[i].user_id,
            action=logs[i].action,
            timestamp=logs[i].timestamp,
            details=logs[i].details
        )
        assert logs[i].entry_hash == calculated
    db.close()
