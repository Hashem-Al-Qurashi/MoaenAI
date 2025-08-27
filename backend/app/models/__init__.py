"""
Database models package - Safe imports with relationships added after loading.
"""

from sqlalchemy.orm import relationship

# Import all models first (no relationships yet)
from app.models.user import User
from app.models.consultation import Consultation
from app.models.conversation import Conversation, Message

# Now add relationships AFTER all models are loaded
# This prevents circular import issues

# User relationships
User.consultations = relationship("Consultation", back_populates="user")
User.conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

# Conversation relationships  
Conversation.user = relationship("User", back_populates="conversations")
Conversation.messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

# Message relationships
Message.conversation = relationship("Conversation", back_populates="messages")

# Export all models
__all__ = ["User", "Consultation", "Conversation", "Message"]