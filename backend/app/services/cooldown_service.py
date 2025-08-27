"""
Cooldown service for managing question limits and refill timing.
"""

from datetime import datetime, timedelta
from typing import Tuple, Optional
from sqlalchemy.orm import Session


class CooldownService:
    """Service for managing user question cooldowns and limits"""
    
    COOLDOWN_DURATION_HOURS = 1.5  # 1.2 minutes cooldown
    # Define limits for guest and signed-in users
    GUEST_QUESTION_LIMIT = 7
    SIGNED_IN_QUESTION_LIMIT = 20
    
    @staticmethod
    def get_question_status(db: Session, user) -> dict:
        """Get current question availability status for a user."""
        now = datetime.utcnow()
        
        if user:
            max_questions = CooldownService.SIGNED_IN_QUESTION_LIMIT
            
            # Check if user needs a reset
            if user.cycle_reset_time and now >= user.cycle_reset_time:
                user.questions_used_current_cycle = 0
                user.cycle_reset_time = None
                db.commit()
            
            questions_used = user.questions_used_current_cycle
        else:
            max_questions = CooldownService.GUEST_QUESTION_LIMIT
            questions_used = 0
        
        questions_available = max_questions - questions_used
        is_in_cooldown = questions_available <= 0 and user and user.cycle_reset_time
        
        return {
            "questions_available": max(0, questions_available),
            "questions_used": questions_used,
            "max_questions": max_questions,
            "is_in_cooldown": is_in_cooldown,
            "reset_time": user.cycle_reset_time.isoformat() if user and user.cycle_reset_time else None,
            "can_ask_question": questions_available > 0
        }
    
    @staticmethod
    def can_ask_question(db: Session, user) -> Tuple[bool, str, Optional[datetime]]:
        """Check if user can ask a question right now."""
        status = CooldownService.get_question_status(db, user)
        
        if status["can_ask_question"]:
            return True, "OK", None
        
        if status["is_in_cooldown"]:
            reset_time = datetime.fromisoformat(status["reset_time"])
            return False, f"Questions will refill at {reset_time.strftime('%I:%M %p')}", reset_time
        
        return False, "Question limit reached", None
    
    @staticmethod
    def use_question(db: Session, user) -> bool:
        """Use one question and update cooldown if needed."""
        can_ask, message, reset_time = CooldownService.can_ask_question(db, user)
        
        if not can_ask:
            return False
        
        user.questions_used_current_cycle += 1
        user.last_question_time = datetime.utcnow()
        
        # Check if they've hit the limit
        if user.questions_used_current_cycle >= CooldownService.SIGNED_IN_QUESTION_LIMIT:
            user.cycle_reset_time = datetime.utcnow() + timedelta(hours=CooldownService.COOLDOWN_DURATION_HOURS)
        
        db.commit()
        return True