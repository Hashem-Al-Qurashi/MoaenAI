"""
CLEAN MINIMAL AUTH - Working Version
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
import uuid

from app.database import get_database
from app.models.user import User

router = APIRouter(tags=["authentication"])

# Request schemas
class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: str
    password: str

# Simple password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register")
async def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_database)
):
    """Minimal user registration"""
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(400, "Email already registered")
    
    hashed_pw = hash_password(request.password)
    new_user = User(
        id=str(uuid.uuid4()),
        email=request.email,
        hashed_password=hashed_pw,
        full_name=request.full_name,
        is_active=True,
        is_verified=False,
        subscription_tier="free",
        questions_used_this_month=0
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "id": new_user.id,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "subscription_tier": new_user.subscription_tier,
        "is_active": new_user.is_active,
        "questions_used_this_month": new_user.questions_used_this_month,
        "is_verified": new_user.is_verified
    }

@router.post("/login") 
async def login_user(
    request: LoginRequest,
    db: Session = Depends(get_database)
):
    """Minimal login"""
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    
    fake_token = f"user_{user.id}_{user.email}"
    
    return {
        "access_token": fake_token,
        "refresh_token": fake_token,
        "token_type": "bearer",
        "expires_in": 3600,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "subscription_tier": user.subscription_tier,
            "questions_used_this_month": user.questions_used_this_month,
            "is_verified": user.is_verified,
            "is_active": user.is_active
        }
    }

# Password utilities (moved from auth_service.py)
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)
