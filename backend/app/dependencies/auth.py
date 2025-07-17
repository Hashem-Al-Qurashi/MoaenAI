"""
Authentication dependencies for FastAPI
Supports both required and optional authentication
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import jwt
from datetime import datetime, timezone

from app.database import get_database
from app.models.user import User
from app.core.config import settings

# Security scheme
security = HTTPBearer(auto_error=False)

def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_database)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None
    This allows endpoints to work for both guests and authenticated users
    """
    if not credentials:
        return None
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
            
        # Check token expiration
        exp = payload.get("exp")
        if exp is None or datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
            return None
            
    except jwt.PyJWTError:
        return None
    
    # Get user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    return user

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database)
) -> User:
    """
    Get current user (required authentication)
    Raises HTTPException if not authenticated
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Check token expiration
        exp = payload.get("exp")
        if exp is None or datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user