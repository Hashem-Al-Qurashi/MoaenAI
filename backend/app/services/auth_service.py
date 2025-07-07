"""
Minimal AuthService - Only what chat_service.py needs
"""

from typing import Tuple
from sqlalchemy.orm import Session
from app.models.user import User


class AuthService:
    """Minimal auth service for chat functionality"""

    @staticmethod
    def check_user_limits(db: Session, user_id: str) -> Tuple[bool, str]:
        """
        Check if user can make more requests based on subscription.
        Used by chat_service.py
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "User not found"
        
        # Free tier limits
        if user.subscription_tier == "free":
            if user.questions_used_this_month >= 20:
                return False, "Free tier limit reached (20 questions/month). Please upgrade to Pro."
        
        # Pro tier limits
        elif user.subscription_tier == "pro":
            if user.questions_used_this_month >= 100:
                return False, "Pro tier limit reached (100 questions/month)."
        
        # Enterprise tier: unlimited
        return True, "OK"
