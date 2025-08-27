# backend/app/services/guest_service.py - Enhanced with Conversation Memory

"""
Guest session management for tracking question limits and conversation history.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List


class GuestService:
    """Service for managing guest user question limits and conversation memory"""
    
    # In-memory storage for guest sessions (in production, use Redis)
    guest_sessions = {}
    
    @staticmethod
    def get_guest_session(session_id: str) -> Dict:
        """Get or create guest session data with conversation history"""
        if session_id not in GuestService.guest_sessions:
            GuestService.guest_sessions[session_id] = {
                "questions_used": 0,
                "reset_time": None,
                "created_at": datetime.utcnow(),
                "conversation_history": [],  # 🔥 NEW: Store conversation history
                "last_activity": datetime.utcnow()
            }
        
        # Update last activity
        GuestService.guest_sessions[session_id]["last_activity"] = datetime.utcnow()
        return GuestService.guest_sessions[session_id]
    
    @staticmethod
    def can_guest_ask_question(session_id: str) -> Tuple[bool, str, Optional[datetime]]:
        """Check if guest can ask a question"""
        from app.services.cooldown_service import CooldownService
        
        session = GuestService.get_guest_session(session_id)
        now = datetime.utcnow()
        
        # Check if reset time has passed
        if session["reset_time"] and now >= session["reset_time"]:
            session["questions_used"] = 0
            session["reset_time"] = None
        
        questions_available = CooldownService.GUEST_QUESTION_LIMIT - session["questions_used"]
        
        if questions_available > 0:
            return True, "OK", None
        
        if session["reset_time"]:
            return False, f"Questions will refill at {session['reset_time'].strftime('%I:%M %p')}", session["reset_time"]
        
        return False, "Question limit reached", None
    
    @staticmethod
    def use_guest_question(session_id: str) -> bool:
        """Use one question for guest user"""
        from app.services.cooldown_service import CooldownService
        
        can_ask, message, reset_time = GuestService.can_guest_ask_question(session_id)
        
        if not can_ask:
            return False
        
        session = GuestService.get_guest_session(session_id)
        session["questions_used"] += 1
        
        # Check if they've hit the limit
        if session["questions_used"] >= CooldownService.GUEST_QUESTION_LIMIT:
            session["reset_time"] = datetime.utcnow() + timedelta(hours=CooldownService.COOLDOWN_DURATION_HOURS)
        
        return True
    
    @staticmethod
    def add_message_to_history(session_id: str, role: str, content: str) -> None:
        """Add a message to guest conversation history"""
        session = GuestService.get_guest_session(session_id)
        
        # Ensure conversation_history exists
        if "conversation_history" not in session:
            session["conversation_history"] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        session["conversation_history"].append(message)
        
        # Keep only last 20 messages to prevent memory bloat
        if len(session["conversation_history"]) > 20:
            session["conversation_history"] = session["conversation_history"][-20:]
    
    @staticmethod
    def get_conversation_context(session_id: str, max_messages: int = 10) -> List[Dict[str, str]]:
        """Get conversation context for AI processing"""
        session = GuestService.get_guest_session(session_id)
        
        # Ensure conversation_history exists
        if "conversation_history" not in session:
            session["conversation_history"] = []
            return []
        
        history = session["conversation_history"]
        
        # Get last N messages for context
        recent_messages = history[-max_messages:] if len(history) > max_messages else history
        
        # Format for AI context (remove timestamp)
        context = []
        for message in recent_messages:
            context.append({
                "role": message["role"],
                "content": message["content"]
            })
        
        return context
    
    @staticmethod
    def cleanup_old_sessions(hours_old: int = 24) -> int:
        """Clean up guest sessions older than specified hours"""
        now = datetime.utcnow()
        cutoff_time = now - timedelta(hours=hours_old)
        
        sessions_to_remove = []
        for session_id, session_data in GuestService.guest_sessions.items():
            last_activity = session_data.get("last_activity", session_data.get("created_at"))
            if last_activity < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del GuestService.guest_sessions[session_id]
        
        return len(sessions_to_remove)