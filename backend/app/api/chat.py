# backend/app/api/chat.py - Complete Unified Chat API with Multi-Agent Integration

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

# Multi-agent system availability check
try:
    from multi_agent_legal import EnhancedRAGEngine
    MULTI_AGENT_AVAILABLE = True
    print("✅ Multi-agent system loaded in chat API")
except ImportError as e:
    MULTI_AGENT_AVAILABLE = False
    print(f"⚠️ Multi-agent system not available in chat API: {e}")

router = APIRouter(prefix="/chat", tags=["chat"])


# Add these serializer functions after your imports and before the router definition

def _serialize_user_message(user_message) -> Dict[str, Any]:
    """Convert user message object to serializable dictionary"""
    return {
        'id': str(user_message.id),
        'content': str(user_message.content),
        'timestamp': user_message.created_at.isoformat() if hasattr(user_message, 'created_at') else datetime.utcnow().isoformat(),
        'role': 'user'
    }

def _serialize_ai_message(ai_message) -> Dict[str, Any]:
    """Convert AI message object to serializable dictionary"""
    return {
        'id': str(ai_message.id),
        'content': str(ai_message.content),
        'timestamp': ai_message.created_at.isoformat() if hasattr(ai_message, 'created_at') else datetime.utcnow().isoformat(),
        'role': 'assistant',
        'processing_time_ms': str(getattr(ai_message, 'processing_time_ms', 0))
    }

def _serialize_user_data(current_user: Optional[User]) -> Optional[Dict[str, Any]]:
    """Convert user object to serializable dictionary"""
    if not current_user:
        return None
    
    return {
        'id': str(current_user.id),
        'email': str(current_user.email),
        'full_name': str(current_user.full_name),
        'questions_used_current_cycle': int(current_user.questions_used_current_cycle),
        'cycle_reset_time': current_user.cycle_reset_time.isoformat() if current_user.cycle_reset_time else None,
        'subscription_tier': str(current_user.subscription_tier),
        'is_active': bool(current_user.is_active),
        'is_verified': bool(current_user.is_verified),
        'questions_remaining': int(_calculate_questions_remaining(current_user))
    }

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
    enable_trust_trail: bool = Form(False, description="Enable multi-agent trust trail for transparency"), # 🔥 NEW
    accept: str = Header("application/json", description="Response format: application/json or text/event-stream"),
    db: Session = Depends(get_database),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    🔥 UNIFIED: Send message with smart content negotiation + MULTI-AGENT SUPPORT
    
    - Accept: application/json → Complete response
    - Accept: text/event-stream → Real-time streaming
    - Both modes support full conversation memory for guests and users
    - NEW: Multi-agent legal reasoning for authenticated users with trust trail
    """
    try:
        print(f"🔄 Processing unified message from {'user' if current_user else 'guest'}: {message[:50]}...")
        print(f"📡 Response format requested: {accept}")
        print(f"🔍 Trust trail: {'enabled' if enable_trust_trail else 'disabled'}")
        
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
            # 🔥 STREAMING MODE with Multi-Agent
            return StreamingResponse(
                _generate_streaming_response(
                    db, current_user, session_id, conversation_id, message, user_type, enable_trust_trail # 🔥 NEW PARAM
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
            # 📦 JSON MODE (Complete Response) with Multi-Agent
            return await _generate_json_response(
                db, current_user, session_id, conversation_id, message, user_type, enable_trust_trail # 🔥 NEW PARAM
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
    user_type: str,
    enable_trust_trail: bool = False  # 🔥 NEW PARAMETER
):
    """Generate real-time streaming response with conversation memory + MULTI-AGENT SUPPORT"""
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
        metadata_payload = {
            'type': 'metadata', 
            'id': response_id, 
            'conversation_id': conversation_id, 
            'user_message': {
                'id': user_message.id, 
                'content': message_content, 
                'timestamp': user_message.created_at.isoformat()
            },
            'multi_agent_enabled': MULTI_AGENT_AVAILABLE,
            'trust_trail_enabled': enable_trust_trail
        }
        yield f"data: {json.dumps(metadata_payload)}\n\n"
        
        # ===== ENHANCED AI RESPONSE WITH MULTI-AGENT =====
        full_response = ""
        chunk_count = 0
        multi_agent_metadata = {}
        processing_mode = "standard"
        

        print(f"🔍 DEBUG ROUTING:")
        print(f"  current_user: {bool(current_user)}")
        print(f"  MULTI_AGENT_AVAILABLE: {MULTI_AGENT_AVAILABLE}")
        print(f"  enable_trust_trail: {enable_trust_trail}")
        print(f"  Will use multi-agent: {bool(current_user and MULTI_AGENT_AVAILABLE)}")
        # 🚀 TRY MULTI-AGENT FOR AUTHENTICATED USERS WITH TRUST TRAIL
        if MULTI_AGENT_AVAILABLE:
            try:
                user_identifier = current_user.email if current_user else f"guest_{session_id}"
                print(f"🤖 Using multi-agent streaming for {user_identifier}")
                if not current_user:
                    print(f"🔍 GUEST DEBUG:")
                    print(f"  session_id: {session_id}")
                    print(f"  context length: {len(context)}")
                    print(f"  message_content: {message_content[:50]}...")
                enhanced_rag = EnhancedRAGEngine()
                processing_mode = "multi_agent"
                print(f"🔄 Starting multi-agent processing...")
                async for chunk in enhanced_rag.ask_question_with_multi_agent(
                    query=message_content,
                    conversation_context=context,
                    enable_trust_trail=enable_trust_trail
                ):
                    print(f"🔍 Received chunk: {chunk[:50]}...")  
                    if chunk.startswith("data: "):
                        # Parse metadata chunks
                        try:
                            chunk_data = json.loads(chunk[6:])
                            if chunk_data.get("type") == "multi_agent_metadata":
                                multi_agent_metadata.update(chunk_data)
                                # Send multi-agent metadata to frontend
                                yield f"data: {json.dumps({'type': 'multi_agent_metadata', **chunk_data})}\n\n"
                            elif chunk_data.get("type") == "trust_trail":
                                multi_agent_metadata["trust_trail"] = chunk_data
                                # Send trust trail data to frontend
                                yield f"data: {json.dumps({'type': 'trust_trail', **chunk_data})}\n\n"
                        except Exception as parse_error:
                            print(f"⚠️ Failed to parse metadata chunk: {parse_error}")
                    else:
                        # Regular content chunks
                        if chunk and chunk.strip():
                            full_response += chunk
                            chunk_count += 1
                            
                            chunk_data = {
                                'type': 'chunk',
                                'content': chunk,
                                'chunk_id': chunk_count,
                                'multi_agent': True  # 🔥 Flag for frontend
                            }
                            yield f"data: {json.dumps(chunk_data)}\n\n"
                
                print(f"✅ Multi-agent streaming completed: {len(full_response)} chars")
                
            except Exception as multi_agent_error:
                print(f"⚠️ Multi-agent streaming failed: {multi_agent_error}")
                print(f"🔄 Falling back to standard streaming")
                processing_mode = "fallback"
                
                # Reset response for fallback
                full_response = ""
                chunk_count = 0
                
                # Fallback to your existing streaming logic
                from rag_engine import rag_engine
                
                if context and len(context) > 0:
                    stream_iterator = rag_engine.ask_question_with_context_streaming(message_content, context)
                else:
                    stream_iterator = rag_engine.ask_question_streaming(message_content)
                
                async for chunk in stream_iterator:
                    if chunk and chunk.strip():
                        full_response += chunk
                        chunk_count += 1
                        
                        chunk_data = {
                            'type': 'chunk',
                            'content': chunk,
                            'chunk_id': chunk_count,
                            'multi_agent': False  # 🔥 Fallback mode
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"
        
        else:
            # 🌐 STANDARD STREAMING (Guests + Users without trust trail)
            from rag_engine import rag_engine
            
            if context and len(context) > 0:
                print(f"🔄 Standard streaming with context: {len(context)} messages")
                stream_iterator = rag_engine.ask_question_with_context_streaming(message_content, context)
            else:
                print("🔄 Standard streaming without context")
                stream_iterator = rag_engine.ask_question_streaming(message_content)
            
            async for chunk in stream_iterator:
                if chunk and chunk.strip():
                    full_response += chunk
                    chunk_count += 1
                    
                    chunk_data = {
                        'type': 'chunk',
                        'content': chunk,
                        'chunk_id': chunk_count,
                        'multi_agent': False
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
        
        # ===== SAVE AI RESPONSE =====
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        if current_user:
            # Save to database with enhanced metadata
            ai_message = ChatService.add_message(
                db, conversation_id, "assistant", full_response,
                confidence_score=str(multi_agent_metadata.get("overall_confidence", 0.8)),
                processing_time_ms=str(multi_agent_metadata.get("processing_time_ms", processing_time)),
                sources=json.dumps(multi_agent_metadata.get("citations_summary", []))
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

        completion_data = {
        'type': 'complete',
        'id': str(response_id),
        'conversation_id': str(conversation_id) if conversation_id else None,
        'ai_message': _serialize_ai_message(ai_message),
        'updated_user': _serialize_user_data(current_user),
        'session_id': str(session_id) if session_id and not current_user else None,
        'user_type': str(user_type),
        'processing_time_ms': int(processing_time),
        'total_chunks': int(chunk_count),
        # 🔥 ENHANCED METADATA
        'processing_mode': str(processing_mode),
        'multi_agent_enabled': bool(processing_mode == "multi_agent"),
        'overall_confidence': float(multi_agent_metadata.get("overall_confidence", 0.8)),
        'citations_count': int(len(multi_agent_metadata.get("citations_summary", []))),
        'citations_summary': list(multi_agent_metadata.get("citations_summary", [])),
        'reasoning_steps_count': int(multi_agent_metadata.get("total_steps", 0)),
        'trust_trail_enabled': bool(enable_trust_trail),
        'fallback_reason': str(processing_mode) if processing_mode == "fallback" else None
    }
            

            
        try:
            test_json = json.dumps(completion_data)
            print("✅ JSON serialization successful")
        except Exception as e:
            print(f"❌ JSON error: {e}")
            print(f"🔍 Problematic data keys: {list(completion_data.keys())}")        
        # ===== ENHANCED COMPLETION METADATA =====
        
        yield f"data: {json.dumps(completion_data)}\n\n"
        yield "data: [DONE]\n\n"
        
        print(f"✅ Enhanced streaming completed: {chunk_count} chunks, {len(full_response)} characters")
        print(f"📊 Processing mode: {processing_mode}")
        print(f"📊 Citations: {len(multi_agent_metadata.get('citations_summary', []))}")
        
    except Exception as e:
        print(f"❌ Enhanced streaming error: {e}")
        import traceback
        traceback.print_exc()
        error_data = {
            'type': 'error',
            'error': str(e),
            'id': response_id,
            'processing_mode': 'error'
        }
        yield f"data: {json.dumps(error_data)}\n\n"
        yield "data: [DONE]\n\n"

async def _generate_json_response(
    db: Session,
    current_user: Optional[User],
    session_id: Optional[str],
    conversation_id: Optional[str],
    message_content: str,
    user_type: str,
    enable_trust_trail: bool = False  # 🔥 NEW PARAMETER
) -> JSONResponse:
    """Generate complete JSON response with conversation memory + MULTI-AGENT SUPPORT"""
    
    if current_user:
        # 🚀 ENHANCED: Try multi-agent for authenticated users with trust trail
        if enable_trust_trail and MULTI_AGENT_AVAILABLE:
            try:
                print(f"🤖 Using multi-agent JSON processing for {current_user.email}")
                
                # Use ChatService process_chat_message_with_multi_agent if it exists
                try:
                    result = await ChatService.process_chat_message_with_multi_agent(
                        db=db,
                        user=current_user,
                        conversation_id=conversation_id,
                        message_content=message_content,
                        enable_trust_trail=enable_trust_trail
                    )
                    
                    print(f"✅ Multi-agent JSON processing successful")
                    return JSONResponse(content=result)
                    
                except AttributeError:
                    # Fallback if the method doesn't exist yet
                    print(f"⚠️ Multi-agent ChatService method not available, using direct approach")
                    
                    # Direct multi-agent processing
                    enhanced_rag = EnhancedRAGEngine()
                    
                    # Get conversation context
                    if conversation_id:
                        conversation = db.query(Conversation).filter(
                            Conversation.id == conversation_id,
                            Conversation.user_id == current_user.id
                        ).first()
                        if not conversation:
                            raise Exception("Conversation not found")
                        context = ChatService.get_conversation_context(db, conversation_id, 10)
                    else:
                        conversation = ChatService.create_conversation(
                            db, current_user.id,
                            title=message_content[:50] + "..." if len(message_content) > 50 else message_content
                        )
                        conversation_id = conversation.id
                        context = []
                    
                    # Add user message
                    user_message = ChatService.add_message(db, conversation_id, "user", message_content)
                    
                    # Process with multi-agent
                    chunks = []
                    metadata = {}
                    
                    async for chunk in enhanced_rag.ask_question_with_multi_agent(
                        query=message_content,
                        conversation_context=context,
                        enable_trust_trail=enable_trust_trail
                    ):
                        if chunk.startswith("data: "):
                            try:
                                chunk_data = json.loads(chunk[6:])
                                metadata.update(chunk_data)
                            except:
                                pass
                        else:
                            chunks.append(chunk)
                    
                    ai_response = ''.join(chunks)
                    
                    # Save AI response
                    ai_message = ChatService.add_message(
                        db, conversation_id, "assistant", ai_response,
                        confidence_score=str(metadata.get("overall_confidence", 0.8)),
                        processing_time_ms=str(metadata.get("processing_time_ms", 0)),
                        sources=json.dumps(metadata.get("citations_summary", []))
                    )
                    
                    # Update user
                    UserService.increment_question_usage(db, current_user.id)
                    db.refresh(current_user)
                    
                    result = {
                        "conversation_id": conversation_id,
                        "user_message": {
                            "id": user_message.id,
                            "content": message_content,
                            "timestamp": user_message.created_at.isoformat()
                        },
                        "ai_message": {
                            "id": ai_message.id,
                            "content": ai_response,
                            "timestamp": ai_message.created_at.isoformat()
                        },
                        "updated_user": {
                            'id': current_user.id,
                            'email': current_user.email,
                            'full_name': current_user.full_name,
                            'questions_used_current_cycle': current_user.questions_used_current_cycle,
                            'cycle_reset_time': current_user.cycle_reset_time.isoformat() if current_user.cycle_reset_time else None,
                            'subscription_tier': current_user.subscription_tier,
                            'is_active': current_user.is_active,
                            'is_verified': current_user.is_verified,
                            'questions_remaining': _calculate_questions_remaining(current_user)
                        },
                        # Multi-agent metadata
                        "multi_agent_enabled": True,
                        "processing_mode": "multi_agent",
                        "overall_confidence": metadata.get("overall_confidence", 0.8),
                        "citations_count": len(metadata.get("citations_summary", [])),
                        "citations_summary": metadata.get("citations_summary", []),
                        "trust_trail_data": metadata.get("trust_trail", {}),
                        "trust_trail_enabled": enable_trust_trail
                    }
                    
                    return JSONResponse(content=result)
                    
            except Exception as multi_agent_error:
                print(f"⚠️ Multi-agent JSON processing failed: {multi_agent_error}")
                print(f"🔄 Falling back to standard processing")
        
        # Use existing ChatService for authenticated users (fallback)
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
        
        # Add fallback metadata
        result.update({
            "multi_agent_enabled": False,
            "processing_mode": "standard",
            "overall_confidence": 0.8,
            "citations_count": 0,
            "citations_summary": [],
            "trust_trail_enabled": False
        })
        
        return JSONResponse(content=result)
        
    else:
        # Handle guest users with session-based memory (unchanged)
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
            "user_type": user_type,
            # Guest users don't get multi-agent
            "multi_agent_enabled": False,
            "processing_mode": "guest",
            "trust_trail_enabled": False
        }
        
        return JSONResponse(content=result)

# 🔥 NEW: Multi-agent system status endpoint
@router.get("/system-status")
async def get_enhanced_system_status():
    """Get comprehensive system status including multi-agent capabilities"""
    
    try:
        # Test multi-agent system
        multi_agent_status = "unavailable"
        api_status = "disconnected"
        
        if MULTI_AGENT_AVAILABLE:
            try:
                enhanced_rag = EnhancedRAGEngine()
                multi_agent_status = "available"
                api_status = "connected"
            except Exception as e:
                multi_agent_status = f"error: {str(e)}"
        
        return {
            "system_status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "multi_agent_system": {
                "available": MULTI_AGENT_AVAILABLE,
                "status": multi_agent_status,
                "api_status": api_status
            },
            "features": {
                "conversation_memory": True,
                "guest_access": True,
                "streaming_responses": True,
                "content_negotiation": True,
                "trust_trail": MULTI_AGENT_AVAILABLE,
                "citation_validation": MULTI_AGENT_AVAILABLE,
                "multi_agent_reasoning": MULTI_AGENT_AVAILABLE,
                "arabic_legal_expertise": True
            },
            "api_endpoints": {
                "unified_chat": "/api/chat/message",
                "conversations": "/api/chat/conversations", 
                "messages": "/api/chat/conversations/{id}/messages",
                "status": "/api/chat/status",
                "system_status": "/api/chat/system-status"
            }
        }
        
    except Exception as e:
        return {
            "system_status": "degraded",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "multi_agent_system": {
                "available": False,
                "status": "error"
            }
        }

# 🔥 NEW: Simple multi-agent test endpoint
@router.post("/test-multi-agent")
async def test_multi_agent_system(
    test_query: str = Form("موظف تم فصله بدون مبرر، ما حقوقه القانونية؟"),
    enable_trust_trail: bool = Form(True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_database)
):
    """Test endpoint for multi-agent legal reasoning system"""
    
    if not MULTI_AGENT_AVAILABLE:
        return {
            "test_status": "unavailable",
            "error": "Multi-agent system not loaded",
            "multi_agent_enabled": False
        }
    
    try:
        print(f"🧪 Testing multi-agent system for user: {current_user.email}")
        
        # Test with streaming response collection
        response_chunks = []
        metadata = {}
        
        enhanced_rag = EnhancedRAGEngine()
        
        async for chunk in enhanced_rag.ask_question_with_multi_agent(
            query=test_query,
            enable_trust_trail=enable_trust_trail
        ):
            if chunk.startswith("data: "):
                try:
                    chunk_data = json.loads(chunk[6:])
                    metadata.update(chunk_data)
                except:
                    pass
            else:
                response_chunks.append(chunk)
        
        full_response = ''.join(response_chunks)
        
        return {
            "test_status": "success",
            "multi_agent_enabled": True,
            "processing_mode": "multi_agent",
            "test_query": test_query,
            "response_length": len(full_response),
            "response_preview": full_response[:300] + "..." if len(full_response) > 300 else full_response,
            "confidence": metadata.get("overall_confidence", 0.0),
            "citations_count": len(metadata.get("citations_summary", [])),
            "reasoning_steps": metadata.get("total_steps", 0),
            "trust_trail_available": bool(metadata.get("trust_trail")),
            "processing_time_ms": metadata.get("processing_time_ms", 0),
            "metadata": metadata
        }
        
    except Exception as e:
        return {
            "test_status": "failed",
            "error": str(e),
            "multi_agent_enabled": False,
            "test_query": test_query
        }

# Keep all your existing endpoints unchanged
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
            "processing_time_ms": msg.processing_time_ms,
            "sources": json.loads(msg.sources) if msg.sources else []  # 🔥 Enhanced with citations
        })
    
    return {
        "conversation_id": conversation_id,
        "conversation_title": conversation.title,
        "messages": message_list,
        "total_messages": len(message_list)
    }

@router.get("/conversations/{conversation_id}/trust-trail")
async def get_conversation_trust_trail(
    conversation_id: str,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """
    🔥 NEW: Get detailed trust trail for a conversation
    Useful for conservative law firms that want to review reasoning post-consultation
    """
    try:
        # Verify user owns the conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get all assistant messages with enhanced metadata
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.role == "assistant"
        ).order_by(
            Message.created_at.asc()
        ).all()
        
        # Extract trust trail data from messages
        trust_trail_messages = []
        for message in messages:
            try:
                citations = json.loads(message.sources) if message.sources else []
                trust_trail_messages.append({
                    "message_id": message.id,
                    "content": message.content,
                    "timestamp": message.created_at.isoformat(),
                    "confidence_score": float(message.confidence_score) if message.confidence_score else 0.8,
                    "processing_time_ms": int(message.processing_time_ms) if message.processing_time_ms else 0,
                    "citations": citations,
                    "has_trust_trail": len(citations) > 0
                })
            except Exception as parse_error:
                print(f"⚠️ Error parsing message metadata: {parse_error}")
                # Include message with basic info
                trust_trail_messages.append({
                    "message_id": message.id,
                    "content": message.content,
                    "timestamp": message.created_at.isoformat(),
                    "confidence_score": 0.8,
                    "processing_time_ms": 0,
                    "citations": [],
                    "has_trust_trail": False
                })
        
        return {
            "conversation_id": conversation_id,
            "conversation_title": conversation.title,
            "trust_trail_messages": trust_trail_messages,
            "total_messages": len(trust_trail_messages),
            "total_citations": sum(len(msg["citations"]) for msg in trust_trail_messages),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Trust trail fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trust trail")

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
            "user_type": "authenticated",
            "multi_agent_available": MULTI_AGENT_AVAILABLE  # 🔥 Enhanced status
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
            "user_type": "guest",
            "multi_agent_available": False  # Guests don't get multi-agent
        }
    else:
        raise HTTPException(status_code=400, detail="Session ID required for guest users")