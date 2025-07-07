"""
Simple consultations router - minimal working version
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.database import get_database
from app.models.user import User

router = APIRouter(tags=["consultations"])

@router.post("/ask")
async def ask_legal_question(
    query: str = Form(..., description="Legal question in Arabic"),
    db: Session = Depends(get_database)
):
    """Simple legal question endpoint"""
    try:
        # Import RAG engine
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from rag_engine import ask_question
        
        print(f"🤖 Processing question: {query[:50]}...")
        
        # Get first user for guest mode
        current_user = db.query(User).first()
        
        # Process the question
        start_time = datetime.now()
        answer = ask_question(query.strip())
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Calculate remaining questions
        questions_remaining = 999
        if current_user:
            if current_user.subscription_tier == "free":
                questions_remaining = max(0, 20 - current_user.questions_used_this_month)
        
        return {
            "id": str(uuid.uuid4()),
            "question": query.strip(),
            "answer": answer,
            "category": "general",
            "processing_time_ms": int(processing_time),
            "timestamp": datetime.now().isoformat(),
            "user_questions_remaining": questions_remaining
        }
        
    except Exception as e:
        print(f"❌ Error processing question: {e}")
        raise HTTPException(500, f"Error processing question: {str(e)}")

@router.get("/categories")
async def get_legal_categories():
    """Get available legal categories"""
    return {
        "categories": [
            {"id": "commercial", "name": "القانون التجاري", "emoji": "💼"},
            {"id": "labor", "name": "قانون العمل", "emoji": "👷"},
            {"id": "real_estate", "name": "القانون العقاري", "emoji": "🏠"},
            {"id": "family", "name": "الأحوال الشخصية", "emoji": "👨‍👩‍👧‍👦"},
            {"id": "criminal", "name": "القانون الجنائي", "emoji": "⚖️"},
            {"id": "administrative", "name": "القانون الإداري", "emoji": "🏛️"},
            {"id": "general", "name": "استشارة عامة", "emoji": "📋"}
        ]
    }
