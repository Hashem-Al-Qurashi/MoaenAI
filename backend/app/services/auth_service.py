"""
Complete AuthService implementation with JWT support.
This replaces your minimal auth_service.py with a full implementation.
"""

from typing import Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin
from app.core.security import create_access_token, create_refresh_token, verify_token, verify_refresh_token
from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Complete authentication service with JWT support"""

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            db: Database session
            email: User email
            password: Plain text password
            
        Returns:
            User if authentication successful, None otherwise
        """
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
            
        if not AuthService.verify_password(password, user.hashed_password):
            return None
            
        return user

    @staticmethod
    def register_user(db: Session, user_register: UserRegister) -> Optional[User]:
        """
        Register a new user.
        
        Args:
            db: Database session
            user_register: User registration data
            
        Returns:
            Created user or None if email already exists
        """
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_register.email).first()
        if existing_user:
            return None
        
        # Hash password
        hashed_password = AuthService.hash_password(user_register.password)
        
        # Create user
        db_user = User(
            email=user_register.email,
            hashed_password=hashed_password,
            full_name=user_register.full_name,
            is_active=True,
            is_verified=False,
            subscription_tier="free",
            questions_used_this_month=0
        )
        
        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            print(f"✅ User created: {db_user.id} with name: {db_user.full_name}")
            return db_user
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            db.rollback()
            return None

    @staticmethod
    def login_user(db: Session, user_login: UserLogin) -> Optional[Tuple[User, str, str]]:
        """
        Login user and generate JWT tokens.
        
        Args:
            db: Database session
            user_login: Login credentials
            
        Returns:
            Tuple of (user, access_token, refresh_token) or None
        """
        # Authenticate user
        user = AuthService.authenticate_user(db, user_login.email, user_login.password)
        if not user:
            return None
        
        # Generate tokens
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        
        return user, access_token, refresh_token

    @staticmethod
    def get_current_user(db: Session, token: str) -> Optional[User]:
        """
        Get current user from JWT token.
        
        Args:
            db: Database session
            token: JWT access token
            
        Returns:
            User if token valid, None otherwise
        """
        try:
            # Verify token and get user ID
            user_id = verify_token(token)
            if not user_id:
                return None
            
            # Get user from database
            user = db.query(User).filter(User.id == user_id).first()
            return user
            
        except Exception as e:
            print(f"❌ Error getting current user: {e}")
            return None

    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Optional[Tuple[str, str]]:
        """
        Refresh access token using refresh token.
        
        Args:
            db: Database session
            refresh_token: JWT refresh token
            
        Returns:
            Tuple of (new_access_token, new_refresh_token) or None
        """
        try:
            # Verify refresh token
            user_id = verify_refresh_token(refresh_token)
            if not user_id:
                return None
            
            # Check if user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # Generate new tokens
            new_access_token = create_access_token(subject=user.id)
            new_refresh_token = create_refresh_token(subject=user.id)
            
            return new_access_token, new_refresh_token
            
        except Exception as e:
            print(f"❌ Error refreshing token: {e}")
            return None

    @staticmethod
    def check_user_limits(db: Session, user_id: str) -> Tuple[bool, str]:
        """
        Check if user can make more requests based on subscription.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Tuple of (can_proceed, message)
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"
        
        # Free tier limits
        if user.subscription_tier == "free":
            if False:  # Unlimited questions
                return False, "Free tier limit reached (20 questions/month). Please upgrade to Pro."
        
        # Pro tier limits
        elif user.subscription_tier == "pro":
            if False:  # Unlimited questions
                return False, "Pro tier limit reached (100 questions/month)."
        
        # Enterprise tier: unlimited
        return True, "OK"

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)