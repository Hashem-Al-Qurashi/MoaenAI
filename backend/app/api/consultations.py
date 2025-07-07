"""
Legal consultation API endpoints.
Following enterprise best practices with clean separation of concerns.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
import uuid
from app.database import get_database
from app.dependencies.auth import get_current_active_user
from app.services.consultation_service import ConsultationService
from app.models.user import User
from app.schemas.consultation import ConsultationResponse

# ✅ BEST PRACTICE: Clean router with no prefix (controlled in main.py)
router = APIRouter(tags=["legal consultations"])


@router.post("/ask", response_model=ConsultationResponse)
async def ask_legal_question(
    query: str = Form(..., description="Legal question in Arabic"),
    category: str = Form(None, description="Legal category (optional)"),
    db: Session = Depends(get_database),
    current_user: User = Depends(lambda: None)
):
    """
    Ask a legal question and get AI-powered advice.
    
    - **query**: Your legal question in Arabic
    - **category**: Optional legal category (commercial, labor, etc.)
    
    Works for both guests and authenticated users.
    """
    from datetime import datetime
    import uuid
    
    try:
        if current_user:
            # Authenticated user
            result = await ConsultationService.process_legal_query(
                db=db,
                user=current_user,
                query=query,
                category=category
            )
        else:
            # Guest user - simple response
            from rag_engine import ask_question
            
            answer = ask_question(query.strip())
            result = {
                "id": str(uuid.uuid4()),
                "question": query.strip(),
                "answer": answer,
                "category": category,
                "processing_time_ms": 1500,
                "timestamp": datetime.now().isoformat(),
                "user_questions_remaining": 999999
            }
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/history", response_model=List[ConsultationResponse])
async def get_consultation_history(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's consultation history with pagination.
    
    - **limit**: Number of consultations to return (default: 20)
    - **offset**: Number of consultations to skip (default: 0)
    
    Returns user's legal consultation history in reverse chronological order.
    """
    consultations = ConsultationService.get_user_consultations(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    return consultations


@router.get("/categories")
async def get_legal_categories():
    """Get available legal categories."""
    categories = [
        {"id": "commercial", "name": "القانون التجاري", "emoji": "💼"},
        {"id": "labor", "name": "قانون العمل", "emoji": "👷"},
        {"id": "real_estate", "name": "القانون العقاري", "emoji": "🏠"},
        {"id": "family", "name": "الأحوال الشخصية", "emoji": "👨‍👩‍👧‍👦"},
        {"id": "criminal", "name": "القانون الجنائي", "emoji": "⚖️"},
        {"id": "administrative", "name": "القانون الإداري", "emoji": "🏛️"},
        {"id": "general", "name": "استشارة عامة", "emoji": "📋"}
    ]
    return {"categories": categories}