"""
Consultation model for legal Q&A history.
"""

from sqlalchemy import Column, String, Text, Float, Integer, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class Consultation(Base):
    """Legal consultation history model"""
    
    __tablename__ = "consultations"
    
    # Use String for UUID in SQLite
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Content
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    
    # AI metadata
    confidence_score = Column(Float, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    sources = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="consultations")
    
    def __repr__(self):
        return f"<Consultation(user_id='{self.user_id}', category='{self.category}')>"