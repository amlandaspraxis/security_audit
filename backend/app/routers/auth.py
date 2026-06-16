from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token, validate_password_strength
from app.core.permissions import get_current_user, get_current_active_user, require_admin
from app.core.limiter import limiter
from app.models.models import User
from app.schemas.schemas import Token, UserResponse, UserCreate, UserPasswordReset
from app.core.logging import log_activity
from typing import List

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT access token. Login attempts are rate-limited."""
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Log failure attempt
        log_activity(db, user_id=None, action="LOGIN_FAILED", details=f"Failed login attempt for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        log_activity(db, user_id=user.id, action="LOGIN_INACTIVE", details=f"Inactive user attempt: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account"
        )
        
    # Log successful login
    log_activity(db, user_id=user.id, action="LOGIN_SUCCESS", details=f"User {user.username} logged in successfully")
    
    # Generate token (note: users that need password resets can still log in, but are restricted at endpoint layer)
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "must_reset_password": user.must_reset_password
    }

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user. Default role is 'developer'."""
    # Check if username or email already exists
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Validate password complexity
    if not validate_password_strength(user_in.password):
        raise HTTPException(
            status_code=400,
            detail="Password is not strong enough. It must be at least 8 characters long and include uppercase, lowercase, numbers, and special characters."
        )
        
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=user_in.role, # Role can be specified, but typically defaulted in schema validation
        is_active=True,
        must_reset_password=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    log_activity(db, user_id=db_user.id, action="USER_REGISTERED", details=f"New user registered: {db_user.username} with role {db_user.role}")
    return db_user

@router.post("/change-password")
def change_password(pass_in: UserPasswordReset, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Change the user's password. Used for initial password reset and security updates."""
    if not verify_password(pass_in.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
        
    if not validate_password_strength(pass_in.new_password):
        raise HTTPException(
            status_code=400,
            detail="New password is not strong enough."
        )
        
    current_user.hashed_password = hash_password(pass_in.new_password)
    current_user.must_reset_password = False
    db.commit()
    
    log_activity(db, user_id=current_user.id, action="PASSWORD_CHANGED", details=f"User {current_user.username} successfully changed their password")
    return {"message": "Password changed successfully"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve the current user profile (allows access even if must_reset_password is True so they can check status)."""
    return current_user

@router.get("/users", response_model=List[UserResponse])
def list_users(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Admin-only endpoint to list all users in the system."""
    return db.query(User).all()
