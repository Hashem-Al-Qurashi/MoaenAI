"""
Legal consultation service with user tracking and limits.
"""

"""
Legal consultation service with user tracking and limits.
"""

from typing import Optional, Dict, Any, List  # 🔧 ADD "List" here
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.user import User
from app.models.consultation import Consultation
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from rag_engine import ask_question


class ConsultationService:
    """Service for legal consultation operations"""

    @staticmethod
    async def process_legal_query(
        db: Session,
        user: User,
        query: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a legal query with user tracking and limits.
        
        Args:
            db: Database session
            user: Current authenticated user
            query: Legal question
            category: Optional legal category
            
        Returns:
            Dictionary with question, answer, and metadata
            
        Raises:
            Exception: If user limits exceeded or processing fails
        """
        # Check user limits
        can_proceed, limit_message = AuthService.check_user_limits(db, user.id)
        if not can_proceed:
            raise Exception(limit_message)
        
        # Record start time
        start_time = datetime.now()
        
        # Process the question with AI
        try:
            ai_answer = ask_question(query.strip())
        except Exception as e:
            raise Exception(f"حدث خطأ في معالجة السؤال: {str(e)}")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Save consultation to database
        consultation = Consultation(
            user_id=user.id,
            question=query.strip(),
            answer=ai_answer,
            category=category,
            processing_time_ms=int(processing_time),
            confidence_score=0.85,  # Default confidence
            sources=[]  # Will enhance with RAG later
        )
        
        db.add(consultation)
        
        # Increment user's question usage
        UserService.increment_question_usage(db, user.id)
        
        # Commit all changes
        db.commit()
        db.refresh(consultation)
        
        return {
            "id": consultation.id,
            "question": consultation.question,
            "answer": consultation.answer,
            "category": consultation.category,
            "processing_time_ms": consultation.processing_time_ms,
            "timestamp": consultation.created_at.isoformat(),
            "user_questions_remaining": ConsultationService._get_remaining_questions(user)
        }
    
    @staticmethod
    def _get_remaining_questions(user: User) -> int:
        """Calculate remaining questions for user based on subscription."""
        if user.subscription_tier == "free":
            return 999999
        elif user.subscription_tier == "pro":
            return max(0, 100 - user.questions_used_this_month)
        else:  # enterprise
            return 999999  # "unlimited"
    
    @staticmethod
    def get_user_consultations(
        db: Session,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Consultation]:
        """Get user's consultation history with pagination."""
        return db.query(Consultation).filter(
            Consultation.user_id == user_id
        ).order_by(
            Consultation.created_at.desc()
        ).offset(offset).limit(limit).all()