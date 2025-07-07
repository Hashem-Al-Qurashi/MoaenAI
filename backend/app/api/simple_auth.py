"""
MINIMAL WORKING AUTH - JSON Input Version
"""
from app.dependencies.auth import get_current_active_user
from fastapi import Form
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
import uuid
from app.dependencies.auth import get_current_active_user
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

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

@router.post("/register")
async def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_database)
):
    """Minimal user registration - accepts JSON"""
    
    print(f"📝 Simple registration: {request.email}, {request.full_name}")
    
    try:
        # Check if user exists
        existing = db.query(User).filter(User.email == request.email).first()
        if existing:
            raise HTTPException(400, "Email already registered")
        
        # Create user directly
        hashed_pw = hash_password(request.password)
        new_user = User(
            id=str(uuid.uuid4()),
            email=request.email,
            hashed_password=hashed_pw,
            full_name=request.full_name,  # 🔧 Make sure this is properly saved
            is_active=True,
            is_verified=False,
            subscription_tier="free",
            questions_used_this_month=0
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"✅ User created: {new_user.id} with name: {new_user.full_name}")
        
        return {
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,  # 🔧 Return the actual name
            "subscription_tier": new_user.subscription_tier,
            "is_active": new_user.is_active,
            "questions_used_this_month": new_user.questions_used_this_month,
            "is_verified": new_user.is_verified
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Registration error: {e}")
        db.rollback()
        raise HTTPException(500, f"Registration failed: {str(e)}")

@router.post("/login")
async def login_user(
    request: LoginRequest,
    db: Session = Depends(get_database)
):
    """Minimal login - returns token-like response"""
    
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not pwd_context.verify(request.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    
    # 🔧 FIXED: Return token-like response for frontend compatibility
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

