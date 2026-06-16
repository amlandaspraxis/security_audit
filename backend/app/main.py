import os
import secrets
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app.core.limiter import limiter
from app.models.models import User, Framework, Control
from app.routers import auth, assets, compliance, findings, reports, dashboard

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("compliance_platform")

# Initialize FastAPI app
app = FastAPI(
    title="Security Audit & Compliance Platform",
    description="API backend for tracking assets, controls, audits, and security findings.",
    version="1.0.0"
)

# Attach rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Middleware for Security Headers
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Include API routers
app.include_router(auth.router)
app.include_router(assets.router)
app.include_router(compliance.router)
app.include_router(findings.router)
app.include_router(reports.router)
app.include_router(dashboard.router)

# Seed Database
def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Seed initial admin user if empty
        if db.query(User).count() == 0:
            # Generate secure one-time password
            otp = secrets.token_urlsafe(12)
            hashed_otp = hash_password(otp)
            
            admin_user = User(
                username="admin",
                email="admin@compliance.com",
                hashed_password=hashed_otp,
                role="admin",
                is_active=True,
                must_reset_password=True
            )
            db.add(admin_user)
            db.commit()
            
            # Print very visible console alert
            print("\n" + "="*80)
            print(" SECURITY ALERT: INITIAL ADMIN ACCOUNT CREATED")
            print(" Username: admin")
            print(f" Temporary Password: {otp}")
            print(" Note: You MUST change this password upon first login.")
            print("="*80 + "\n")
            
            # Write to a file in workspace so it's not lost
            workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            setup_file = os.path.join(workspace_dir, "admin_setup.txt")
            with open(setup_file, "w") as f:
                f.write(f"=== INITIAL ADMIN CREDENTIALS ===\nUsername: admin\nPassword: {otp}\n(Change on first login)\n")
            logger.info(f"Seeded admin credentials saved to {setup_file}")

        # 2. Seed Compliance Frameworks & Controls if empty
        if db.query(Framework).count() == 0:
            logger.info("Seeding default compliance frameworks...")
            
            # SOC 2 Framework
            soc2 = Framework(
                name="SOC 2",
                version="2017",
                description="Trust Services Criteria for Security, Availability, Processing Integrity, Confidentiality, and Privacy."
            )
            db.add(soc2)
            db.commit()
            db.refresh(soc2)
            
            soc2_controls = [
                Control(framework_id=soc2.id, section_code="CC6.1", title="Logical Access Controls", description="The entity restricts logical access to system components, physical assets, and data to authorized users."),
                Control(framework_id=soc2.id, section_code="CC6.2", title="User Registration and Authorization", description="The entity registers and authorizes new users before granting logical access."),
                Control(framework_id=soc2.id, section_code="CC6.3", title="Role-Based Access Modification", description="The entity modifies or revokes logical access credentials upon termination or job change."),
                Control(framework_id=soc2.id, section_code="CC6.7", title="Transmission Security", description="The entity protects data in transmission using encryption technologies."),
            ]
            db.add_all(soc2_controls)
            
            # ISO 27001 Framework
            iso = Framework(
                name="ISO 27001",
                version="2022",
                description="International standard for Information Security Management Systems (ISMS)."
            )
            db.add(iso)
            db.commit()
            db.refresh(iso)
            
            iso_controls = [
                Control(framework_id=iso.id, section_code="A.5.15", title="Access Control Policy", description="Access control rules and rights must be established and documented according to security requirements."),
                Control(framework_id=iso.id, section_code="A.8.20", title="Network Security", description="Networks and network services must be secured, managed, and controlled to protect information."),
                Control(framework_id=iso.id, section_code="A.8.24", title="Use of Cryptography", description="Rules for the effective use of cryptography, including key management, must be defined and implemented."),
            ]
            db.add_all(iso_controls)

            # OWASP ASVS Framework
            asvs = Framework(
                name="OWASP ASVS",
                version="4.0.3",
                description="Application Security Verification Standard for testing web application security controls."
            )
            db.add(asvs)
            db.commit()
            db.refresh(asvs)
            
            asvs_controls = [
                Control(framework_id=asvs.id, section_code="V1.1", title="Secure Software Development Lifecycle", description="Ensure that security requirements are defined, tracked, and validated throughout software creation."),
                Control(framework_id=asvs.id, section_code="V2.1", title="Authentication Strength", description="Verify that passwords are processed securely and weak password criteria are rejected."),
                Control(framework_id=asvs.id, section_code="V5.1", title="Input Validation", description="Ensure all user-supplied input is validated and sanitized prior to parsing or storage."),
            ]
            db.add_all(asvs_controls)
            
            db.commit()
            logger.info("Compliance frameworks seeded successfully!")
            
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    seed_database()
