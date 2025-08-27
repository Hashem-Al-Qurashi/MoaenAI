"""
User model for authentication and user management.
"""

from sqlalchemy import Boolean, Column, String, Integer, DateTime, func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class User(Base):
    """User account model"""
    
    __tablename__ = "users"
    
    # Use String for UUID in SQLite
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Subscription management
    subscription_tier = Column(String(50), default="free", nullable=False)
    questions_used_this_month = Column(Integer, default=0, nullable=False)
    
    # Cooldown system
    questions_used_current_cycle = Column(Integer, default=0, nullable=False)
    cycle_reset_time = Column(DateTime(timezone=True), nullable=True)
    last_question_time = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 🔧 ONLY LEGACY RELATIONSHIP FOR NOW
    # conversations relationship will be added dynamically in __init__.py
    
    def __repr__(self):
        return f"<User(email='{self.email}', tier='{self.subscription_tier}')>"