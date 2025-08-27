"""
Consultation schemas for API validation.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class ConsultationResponse(BaseModel):
    """Response schema for legal consultations."""
    
    id: str = Field(..., description="Consultation unique identifier")
    question: str = Field(..., description="Legal question")
    answer: str = Field(..., description="AI-generated legal advice")
    category: Optional[str] = Field(None, description="Legal category")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    timestamp: str = Field(..., description="Consultation timestamp")
    user_questions_remaining: int = Field(..., description="Remaining questions for user")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "question": "ما هي حقوق الموظف عند إنهاء الخدمة؟",
                "answer": "حسب نظام العمل السعودي...",
                "category": "labor",
                "processing_time_ms": 1500,
                "timestamp": "2025-06-29T12:00:00",
                "user_questions_remaining": 2
            }
        }