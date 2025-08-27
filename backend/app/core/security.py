"""
Security utilities for password hashing and JWT token management.
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, int], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: User identifier (usually user ID or email)
        expires_delta: Token expiration time (optional)
    
    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        User subject (ID/email) if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        
        subject: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if subject is None or token_type != "access":
            return None
            
        return subject
        
    except JWTError:
        return None


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Bcrypt hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Bcrypt hashed password
    
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_refresh_token(subject: Union[str, int]) -> str:
    """
    Create a JWT refresh token (longer expiration).
    
    Args:
        subject: User identifier
    
    Returns:
        JWT refresh token string
    """
    expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def verify_refresh_token(token: str) -> Optional[str]:
    """
    Verify and decode JWT refresh token.
    
    Args:
        token: JWT refresh token string
    
    Returns:
        User subject if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        subject: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if subject is None or token_type != "refresh":
            return None
            
        return subject
        
    except JWTError:
        return None