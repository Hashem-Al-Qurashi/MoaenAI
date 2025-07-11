"""
Modern streaming consultations API - Fixed SSE Format
"""
from fastapi import APIRouter, Depends, HTTPException, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import uuid
import json
from datetime import datetime
from rag_engine import rag_engine
from app.database import get_database
from app.models.user import User
from rag_engine import ask_question  # ← This exists and works

router = APIRouter(tags=["consultations"])

@router.post("/ask")
async def ask_legal_question_streaming(
    query: str = Form(..., description="Legal question in Arabic"),
    db: Session = Depends(get_database)
):
    """Modern streaming legal question endpoint with proper SSE format"""
    try:
        print(f"🤖 Processing streaming question: {query[:50]}...")
        
        # Get user info for metadata
        current_user = db.query(User).first()
        questions_remaining = 999
        if current_user and current_user.subscription_tier == "free":
            questions_remaining = max(0, 20 - current_user.questions_used_this_month)
        
        # Create response metadata
        response_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        async def generate_streaming_response():
            """Generate Server-Sent Events stream with proper formatting"""
            try:
                # Send initial metadata
                yield f"data: {json.dumps({'type': 'metadata', 'id': response_id, 'question': query.strip()})}\n\n"
                
                # Stream AI response chunks with proper error handling
                full_response = ""
                chunk_count = 0
                
                async for chunk in rag_engine.ask_question_streaming(query.strip()):
                    if chunk and chunk.strip():  # Only send non-empty chunks
                        full_response += chunk
                        chunk_count += 1
                        
                        # Format as proper SSE
                        chunk_data = {
                            'type': 'chunk', 
                            'content': chunk,
                            'chunk_id': chunk_count
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Send completion metadata
                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                completion_data = {
                    'type': 'complete',
                    'id': response_id,
                    'question': query.strip(),
                    'answer': full_response,
                    'category': 'general',
                    'processing_time_ms': int(processing_time),
                    'timestamp': datetime.now().isoformat(),
                    'user_questions_remaining': questions_remaining,
                    'total_chunks': chunk_count
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
                yield "data: [DONE]\n\n"
                
                print(f"✅ Streaming completed: {chunk_count} chunks, {len(full_response)} characters")
                
            except Exception as stream_error:
                print(f"❌ Streaming generation error: {stream_error}")
                # Send error as SSE
                error_data = {
                    'type': 'error',
                    'error': str(stream_error),
                    'message': 'حدث خطأ أثناء معالجة السؤال'
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_streaming_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except Exception as e:
        print(f"❌ Error in streaming setup: {e}")
        raise HTTPException(500, f"Streaming setup error: {str(e)}")

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