# backend/app/api/chat.py - Complete Unified Chat API

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Form, Query, Header
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
import json
import uuid
from datetime import datetime

from app.database import get_database
from app.dependencies.simple_auth import get_current_active_user, get_optional_current_user
from app.services.chat_service import ChatService
from app.services.cooldown_service import CooldownService
from app.services.guest_service import GuestService
from app.services.user_service import UserService
from app.models.user import User
from app.models.conversation import Conversation, Message

router = APIRouter(prefix="/chat", tags=["chat"])

def _calculate_questions_remaining(user: User) -> int:
    """Calculate remaining questions for user based on subscription."""
    if user.subscription_tier == "free":
        return max(0, 20 - user.questions_used_current_cycle)
    elif user.subscription_tier == "pro":
        return 999999
    else:  # enterprise
        return 999999

@router.post("/message")
async def send_unified_chat_message(
    message: str = Form(..., description="User message"),
    conversation_id: Optional[str] = Form(None, description="Existing conversation ID (optional)"),
    session_id: Optional[str] = Form(None, description="Guest session ID (for guests only)"),
    accept: str = Header("application/json", description="Response format: application/json or text/event-stream"),
    db: Session = Depends(get_database),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    🔥 UNIFIED: Send message with smart content negotiation
    
    - Accept: application/json → Complete response
    - Accept: text/event-stream → Real-time streaming
    - Both modes support full conversation memory for guests and users
    """
    try:
        print(f"🔄 Processing unified message from {'user' if current_user else 'guest'}: {message[:50]}...")
        print(f"📡 Response format requested: {accept}")
        
        # ===== AUTHENTICATION & LIMITS =====
        if current_user:
            # Authenticated user flow
            user_type = "authenticated"
            user_identifier = current_user.email
            
            # Check cooldown for authenticated users
            can_ask, cooldown_message, reset_time = CooldownService.can_ask_question(db, current_user)
            if not can_ask:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "message": cooldown_message,
                        "reset_time": reset_time.isoformat() if reset_time else None,
                        "user_type": user_type
                    }
                )
            
            # Use question for authenticated user
            if not CooldownService.use_question(db, current_user):
                raise HTTPException(status_code=500, detail="Failed to process question")
                
        else:
            # Guest user flow
            user_type = "guest"
            
            if not session_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Session ID required for guest users"
                )
            
            user_identifier = f"guest_{session_id}"
            
            # Check cooldown for guest users
            can_ask, cooldown_message, reset_time = GuestService.can_guest_ask_question(session_id)
            if not can_ask:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "message": cooldown_message,
                        "reset_time": reset_time.isoformat() if reset_time else None,
                        "user_type": user_type
                    }
                )
            
            # Use question for guest user
            if not GuestService.use_guest_question(session_id):
                raise HTTPException(status_code=500, detail="Failed to process question")
        
        # ===== CONTENT NEGOTIATION =====
        if "text/event-stream" in accept:
            # 🔥 STREAMING MODE
            return StreamingResponse(
                _generate_streaming_response(
                    db, current_user, session_id, conversation_id, message, user_type
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Cache-Control"
                }
            )
        else:
            # 📦 JSON MODE (Complete Response)
            return await _generate_json_response(
                db, current_user, session_id, conversation_id, message, user_type
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions (cooldown, etc.)
        raise
    except Exception as e:
        # Rollback question usage on error
        if current_user:
            current_user.questions_used_current_cycle -= 1
            if current_user.questions_used_current_cycle <= 0:
                current_user.cycle_reset_time = None
            db.commit()
        elif session_id:
            guest_session = GuestService.get_guest_session(session_id)
            guest_session["questions_used"] -= 1
        
        print(f"❌ Error processing message: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI processing failed: {str(e)}"
        )

async def _generate_streaming_response(
    db: Session,
    current_user: Optional[User],
    session_id: Optional[str],
    conversation_id: Optional[str],
    message_content: str,
    user_type: str
):
    """Generate real-time streaming response with conversation memory"""
    response_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    try:
        # ===== CONVERSATION SETUP =====
        if current_user:
            # Authenticated user: Database conversations
            if conversation_id:
                conversation = db.query(Conversation).filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == current_user.id
                ).first()
                if not conversation:
                    raise Exception("Conversation not found")
            else:
                # Create new conversation
                conversation = ChatService.create_conversation(
                    db, current_user.id,
                    title=message_content[:50] + "..." if len(message_content) > 50 else message_content
                )
                conversation_id = conversation.id
            
            # Add user message to database
            user_message = ChatService.add_message(
    db, conversation_id, "user", message_content
)
            
            # Get conversation context
            context = ChatService.get_conversation_context(db, conversation_id, 10)
            
        else:
            # Guest user: Session-based conversations
            session = GuestService.get_guest_session(session_id)
            
            # Add conversation_history if it doesn't exist
            if "conversation_history" not in session:
                session["conversation_history"] = []
            
            # Add user message to session history
            session["conversation_history"].append({
                "role": "user",
                "content": message_content,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Keep only last 20 messages to prevent memory bloat
            if len(session["conversation_history"]) > 20:
                session["conversation_history"] = session["conversation_history"][-20:]
            
            # Get context from session (last 10 messages, excluding current)
            history = session["conversation_history"]
            recent_messages = history[-11:-1] if len(history) > 10 else history[:-1]  # Exclude current message
            context = [{"role": msg["role"], "content": msg["content"]} for msg in recent_messages]
            
            # Create mock user message for response
            user_message = type('obj', (object,), {
                'id': f"guest_msg_{int(datetime.utcnow().timestamp())}",
                'content': message_content,
                'created_at': datetime.utcnow()
            })()
        
        # ===== SEND INITIAL METADATA =====
        yield f"data: {json.dumps({'type': 'metadata', 'id': response_id, 'conversation_id': conversation_id, 'user_message': {'id': user_message.id, 'content': message_content, 'timestamp': user_message.created_at.isoformat()}})}\n\n"
        
        # ===== STREAM AI RESPONSE =====
        from rag_engine import rag_engine
        
        full_response = ""
        chunk_count = 0
        
        # Choose streaming method based on context
        if context and len(context) > 0:
            print(f"🔄 Streaming with context: {len(context)} messages")
            stream_iterator = rag_engine.ask_question_with_context_streaming(message_content, context)
        else:
            print("🔄 Streaming without context (first message)")
            stream_iterator = rag_engine.ask_question_streaming(message_content)
        
        async for chunk in stream_iterator:
            if chunk and chunk.strip():
                full_response += chunk
                chunk_count += 1
                
                # Send chunk as SSE
                chunk_data = {
                    'type': 'chunk',
                    'content': chunk,
                    'chunk_id': chunk_count
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
        
        # ===== SAVE AI RESPONSE =====
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        if current_user:
            # Save to database
            ai_message = ChatService.add_message(
    db, conversation_id, "assistant", full_response,
    confidence_score="high",
    processing_time_ms=str(processing_time)
)
            
            # Increment user question usage
            UserService.increment_question_usage(db, current_user.id)
            
            # Refresh user data
            db.refresh(current_user)
            
        else:
            # Save to session
            session["conversation_history"].append({
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Create mock AI message
            ai_message = type('obj', (object,), {
                'id': f"guest_ai_{int(datetime.utcnow().timestamp())}",
                'content': full_response,
                'created_at': datetime.utcnow(),
                'processing_time_ms': str(processing_time)
            })()
        
        # ===== SEND COMPLETION METADATA =====
        completion_data = {
            'type': 'complete',
            'id': response_id,
            'conversation_id': conversation_id,
            'ai_message': {
                'id': ai_message.id,
                'content': full_response,
                'timestamp': ai_message.created_at.isoformat(),
                'processing_time_ms': ai_message.processing_time_ms
            },
            'updated_user': {
                'id': current_user.id,
                'email': current_user.email,
                'full_name': current_user.full_name,
                'questions_used_current_cycle': current_user.questions_used_current_cycle,
                'cycle_reset_time': current_user.cycle_reset_time.isoformat() if current_user.cycle_reset_time else None,
                'subscription_tier': current_user.subscription_tier,
                'is_active': current_user.is_active,
                'is_verified': current_user.is_verified,
                'questions_remaining': _calculate_questions_remaining(current_user)
            } if current_user else None,
            'session_id': session_id if not current_user else None,
            'user_type': user_type,
            'processing_time_ms': processing_time,
            'total_chunks': chunk_count
        }
        
        yield f"data: {json.dumps(completion_data)}\n\n"
        yield "data: [DONE]\n\n"
        
        print(f"✅ Streaming completed: {chunk_count} chunks, {len(full_response)} characters")
        
    except Exception as e:
        print(f"❌ Streaming error: {e}")
        import traceback
        traceback.print_exc()
        error_data = {
            'type': 'error',
            'error': str(e),
            'id': response_id
        }
        yield f"data: {json.dumps(error_data)}\n\n"
        yield "data: [DONE]\n\n"

async def _generate_json_response(
    db: Session,
    current_user: Optional[User],
    session_id: Optional[str],
    conversation_id: Optional[str],
    message_content: str,
    user_type: str
) -> JSONResponse:
    """Generate complete JSON response with conversation memory"""
    
    if current_user:
        # Use existing ChatService for authenticated users
        result = await ChatService.process_chat_message(
            db=db,
            user=current_user,
            conversation_id=conversation_id,
            message_content=message_content
        )
        
        # Add user data
        db.refresh(current_user)
        result["updated_user"] = {
            'id': current_user.id,
            'email': current_user.email,
            'full_name': current_user.full_name,
            'questions_used_current_cycle': current_user.questions_used_current_cycle,
            'cycle_reset_time': current_user.cycle_reset_time.isoformat() if current_user.cycle_reset_time else None,
            'subscription_tier': current_user.subscription_tier,
            'is_active': current_user.is_active,
            'is_verified': current_user.is_verified,
            'questions_remaining': _calculate_questions_remaining(current_user)
        }
        
        return JSONResponse(content=result)
        
    else:
        # Handle guest users with session-based memory
        from rag_engine import ask_question, ask_question_with_context
        
        # Get session and setup conversation history
        session = GuestService.get_guest_session(session_id)
        if "conversation_history" not in session:
            session["conversation_history"] = []
        
        # Add user message
        session["conversation_history"].append({
            "role": "user",
            "content": message_content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Get context for AI
        history = session["conversation_history"]
        context = [{"role": msg["role"], "content": msg["content"]} for msg in history[:-1]]
        
        # Process with AI
        if context:
            ai_response = await ask_question_with_context(message_content, context)
        else:
            ai_response = await ask_question(message_content)
        
        # Save AI response to session
        session["conversation_history"].append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        result = {
            "session_id": session_id,
            "user_message": {
                "content": message_content,
                "timestamp": datetime.utcnow().isoformat()
            },
            "ai_message": {
                "content": ai_response,
                "timestamp": datetime.utcnow().isoformat()
            },
            "user_type": user_type
        }
        
        return JSONResponse(content=result)

# Keep all your existing endpoints (conversations, messages, etc.) unchanged
@router.get("/conversations")
async def get_user_conversations(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's conversation list with pagination."""
    conversations = ChatService.get_user_conversations(db, current_user.id, limit)
    
    conversation_list = []
    for conv in conversations:
        messages = ChatService.get_conversation_messages(db, conv.id, limit=1)
        last_message = messages[-1] if messages else None
        
        conversation_list.append({
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
            "last_message_preview": (
                last_message.content[:100] + "..." 
                if last_message and len(last_message.content) > 100 
                else last_message.content if last_message else None
            ),
            "message_count": len(ChatService.get_conversation_messages(db, conv.id))
        })
    
    return {
        "conversations": conversation_list,
        "total": len(conversation_list),
        "current_user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "subscription_tier": current_user.subscription_tier,
            "questions_remaining": _calculate_questions_remaining(current_user)
        }
    }

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get messages from a specific conversation."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = ChatService.get_conversation_messages(db, conversation_id, limit)
    
    message_list = []
    for msg in messages:
        message_list.append({
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.created_at.isoformat(),
            "confidence_score": msg.confidence_score,
            "processing_time_ms": msg.processing_time_ms
        })
    
    return {
        "conversation_id": conversation_id,
        "conversation_title": conversation.title,
        "messages": message_list,
        "total_messages": len(message_list)
    }

@router.put("/conversations/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str,
    new_title: str = Form(...),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Update conversation title."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    updated_conversation = ChatService.update_conversation_title(db, conversation_id, new_title.strip())
    
    return {
        "conversation_id": conversation_id,
        "new_title": updated_conversation.title,
        "updated_at": updated_conversation.updated_at.isoformat()
    }

@router.delete("/conversations/{conversation_id}")
async def archive_conversation(
    conversation_id: str,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Archive (soft delete) a conversation."""
    success = ChatService.archive_conversation(db, conversation_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "message": "Conversation archived successfully",
        "conversation_id": conversation_id
    }

@router.get("/status")
async def get_chat_status(
    session_id: Optional[str] = Query(None),
    db: Session = Depends(get_database),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get current chat status for both guests and signed-in users."""
    if current_user:
        return {
            "user_id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "subscription_tier": current_user.subscription_tier,
            "questions_used_current_cycle": current_user.questions_used_current_cycle,
            "questions_remaining": _calculate_questions_remaining(current_user),
            "user_type": "authenticated"
        }
    elif session_id:
        session = GuestService.get_guest_session(session_id)
        can_ask, message, reset_time = GuestService.can_guest_ask_question(session_id)
        
        return {
            "questions_available": CooldownService.GUEST_QUESTION_LIMIT - session["questions_used"],
            "questions_used": session["questions_used"],
            "max_questions": CooldownService.GUEST_QUESTION_LIMIT,
            "can_ask_question": can_ask,
            "reset_time": reset_time.isoformat() if reset_time else None,
            "user_type": "guest"
        }
    else:
        raise HTTPException(status_code=400, detail="Session ID required for guest users")