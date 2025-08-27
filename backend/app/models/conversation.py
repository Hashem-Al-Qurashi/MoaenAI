"""
Conversation model for chat history functionality.
Following WhatsApp/ChatGPT conversation patterns.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class Conversation(Base):
    """
    Conversation thread model - groups related legal consultations
    Like WhatsApp chat threads or ChatGPT conversations
    """
    
    __tablename__ = "conversations"
    
    # Primary identifiers
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Conversation metadata
    title = Column(String(200), nullable=True)  # Auto-generated from first message
    is_active = Column(Boolean, default=True, nullable=False)  # For archiving
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id='{self.id}', title='{self.title}', user_id='{self.user_id}')>"


class Message(Base):
    """
    Individual message in a conversation
    Can be from user or AI assistant
    """
    
    __tablename__ = "messages"
    
    # Primary identifiers
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # AI metadata (for assistant messages)
    confidence_score = Column(String(10), nullable=True)  # "high", "medium", "low"
    processing_time_ms = Column(String(10), nullable=True)
    sources = Column(Text, nullable=True)  # JSON string for now
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(role='{self.role}', content='{preview}')>"