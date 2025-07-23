# backend/app/services/chat_service.py - Enhanced for Guest Support
import json
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import json

from app.models.conversation import Conversation, Message
from app.models.user import User
from app.services.auth_service import AuthService
from rag_engine import ask_question_with_context


# Add these imports at the top of your existing file
try:
    from multi_agent_legal import EnhancedRAGEngine
    MULTI_AGENT_AVAILABLE = True
    print("✅ Multi-agent system loaded successfully")
except ImportError as e:
    MULTI_AGENT_AVAILABLE = False
    print(f"⚠️ Multi-agent system not available: {e}")

class ChatService:
    
    # 🔥 NEW: In-memory session storage for guests
    # Format: {"session_id": [{"role": "user", "content": "..."}, ...]}
    _guest_sessions: Dict[str, List[Dict[str, str]]] = {}
    
    @staticmethod
    def create_conversation(
        db: Session, 
        user_id: str, 
        title: Optional[str] = None
    ) -> Conversation:
        """Create new conversation for authenticated users"""
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title or "محادثة جديدة",
            is_active=True
        )
        
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        return conversation

    @staticmethod
    def get_user_conversations(
        db: Session, 
        user_id: str, 
        limit: int = 50
    ) -> List[Conversation]:
        """Get all active conversations for a user"""
        return db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_active == True
        ).order_by(
            Conversation.updated_at.desc()
        ).limit(limit).all()

    @staticmethod
    def get_conversation_messages(
        db: Session, 
        conversation_id: str, 
        limit: int = 100
    ) -> List[Message]:
        """Get messages from a conversation"""
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at.asc()
        ).limit(limit).all()

    @staticmethod
    def add_message(
        db: Session,
        conversation_id: str,
        role: str,  # 'user' or 'assistant'
        content: str,
        confidence_score: Optional[str] = None,
        processing_time_ms: Optional[str] = None,
        sources: Optional[str] = None
    ) -> Message:
        """Add a message to a conversation"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            confidence_score=confidence_score,
            processing_time_ms=processing_time_ms,
            sources=sources
        )
        
        db.add(message)
        
        # Update conversation's updated_at timestamp
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(message)
        
        return message

    @staticmethod
    def get_conversation_context(
        db: Session, 
        conversation_id: str, 
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        """Get recent conversation context for AI (authenticated users)"""
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at.desc()
        ).limit(max_messages).all()
        
        # Reverse to get chronological order
        messages.reverse()
        
        # Format for AI context
        context = []
        for message in messages:
            context.append({
                "role": message.role,
                "content": message.content
            })
        
        return context

    @staticmethod
    def update_conversation_title(
        db: Session, 
        conversation_id: str, 
        title: str
    ) -> Optional[Conversation]:
        """Update conversation title"""
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        
        if conversation:
            conversation.title = title
            conversation.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(conversation)
        
        return conversation

    @staticmethod
    def archive_conversation(
        db: Session, 
        conversation_id: str, 
        user_id: str
    ) -> bool:
        """Archive (soft delete) a conversation"""
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        
        if conversation:
            conversation.is_active = False
            conversation.updated_at = datetime.utcnow()
            db.commit()
            return True
        
        return False

    # 🔥 NEW: Guest session management
    @staticmethod
    def create_guest_session() -> str:
        """Create a new guest session and return session ID"""
        session_id = f"guest_{uuid.uuid4().hex[:8]}"
        ChatService._guest_sessions[session_id] = []
        return session_id

    @staticmethod
    def add_guest_message(
        session_id: str, 
        role: str, 
        content: str
    ) -> None:
        """Add message to guest session"""
        if session_id not in ChatService._guest_sessions:
            ChatService._guest_sessions[session_id] = []
        
        ChatService._guest_sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last 20 messages per session to prevent memory bloat
        if len(ChatService._guest_sessions[session_id]) > 20:
            ChatService._guest_sessions[session_id] = ChatService._guest_sessions[session_id][-20:]

    @staticmethod
    def get_guest_context(
        session_id: str, 
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        """Get conversation context for guest session"""
        if session_id not in ChatService._guest_sessions:
            return []
        
        messages = ChatService._guest_sessions[session_id]
        
        # Get last N messages for context
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
        
        # Format for AI context (remove timestamp)
        context = []
        for message in recent_messages:
            context.append({
                "role": message["role"],
                "content": message["content"]
            })
        
        return context

    @staticmethod
    async def process_unified_message(
        db: Session,
        user: Optional[User],
        message_content: str,
        conversation_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        🔥 UNIFIED: Process message for both authenticated users and guests
        """
        start_time = datetime.utcnow()
        
        if user:
            # 🔐 AUTHENTICATED USER PATH
            # Check user limits
            can_proceed, limit_message = AuthService.check_user_limits(db, user.id)
            if not can_proceed:
                raise Exception(limit_message)
            
            # Get or create conversation
            if conversation_id:
                conversation = db.query(Conversation).filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user.id
                ).first()
                if not conversation:
                    raise Exception("Conversation not found")
            else:
                # Create new conversation
                conversation = ChatService.create_conversation(
                    db, user.id, 
                    title=message_content[:50] + "..." if len(message_content) > 50 else message_content
                )
                conversation_id = conversation.id
            
            # Add user message to database
            user_message = ChatService.add_message(
                db, conversation_id, "user", message_content
            )
            
            # Get conversation context from database
            context_messages = ChatService.get_conversation_context(db, conversation_id, 10)
            
        else:
            # 🌐 GUEST USER PATH
            if not session_id:
                session_id = ChatService.create_guest_session()
            
            # Add user message to session
            ChatService.add_guest_message(session_id, "user", message_content)
            
            # Get conversation context from session
            context_messages = ChatService.get_guest_context(session_id, 10)
            
            # Create mock user message object for response
            user_message = type('obj', (object,), {
                'id': f"guest_msg_{int(datetime.utcnow().timestamp())}",
                'content': message_content,
                'created_at': datetime.utcnow()
            })()
        
        # 🤖 AI PROCESSING (Same for both user types)
# 🤖 AI PROCESSING - Enhanced with Multi-Agent Support
        try:
            if user:
                # 🚀 AUTHENTICATED USERS: Use multi-agent system
                try:
                    # Try multi-agent processing first
                    enhanced_rag = EnhancedRAGEngine()
                    
                    chunks = []
                    metadata = {}
                    
                    async def collect_enhanced_response():
                        nonlocal metadata
                        
                        async for chunk in enhanced_rag.ask_question_with_multi_agent(
                            query=message_content,
                            conversation_context=context_messages,
                            enable_trust_trail=False  # Default to false for unified processing
                        ):
                            if chunk.startswith("data: "):
                                try:
                                    chunk_data = json.loads(chunk[6:])
                                    metadata.update(chunk_data)
                                except:
                                    pass
                            else:
                                chunks.append(chunk)
                        
                        return ''.join(chunks)
                    
                    ai_response = await collect_enhanced_response()
                    print(f"✅ Multi-agent processing successful for authenticated user")
                    
                except Exception as multi_agent_error:
                    print(f"⚠️ Multi-agent failed, fallback to standard: {multi_agent_error}")
                    # Fallback to existing method
                    from rag_engine import ask_question_with_context
                    ai_response = await ask_question_with_context(
                        message_content,
                        context_messages
                    )
            else:
                # 🌐 GUESTS: Use standard processing (for now)
                from rag_engine import ask_question_with_context
                ai_response = await ask_question_with_context(
                    message_content,
                    context_messages
                )
            
            processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            if user:
                # Save AI response to database
                ai_message = ChatService.add_message(
                    db, conversation_id, "assistant", ai_response,
                    processing_time_ms=str(processing_time)
                )
                
                # Update user question count
                from app.services.user_service import UserService
                UserService.increment_question_usage(db, user.id)
                
            else:
                # Add AI response to guest session
                ChatService.add_guest_message(session_id, "assistant", ai_response)
                
                # Create mock AI message object
                ai_message = type('obj', (object,), {
                    'id': f"guest_ai_{int(datetime.utcnow().timestamp())}",
                    'content': ai_response,
                    'created_at': datetime.utcnow(),
                    'processing_time_ms': str(processing_time)
                })()
            
            # 📊 UNIFIED RESPONSE FORMAT
            return {
                "conversation_id": conversation_id if user else None,
                "session_id": session_id if not user else None,
                "user_message": {
                    "id": user_message.id,
                    "content": user_message.content,
                    "timestamp": user_message.created_at.isoformat(),
                    "role": "user"
                },
                "ai_message": {
                    "id": ai_message.id,
                    "content": ai_message.content,
                    "timestamp": ai_message.created_at.isoformat(),
                    "role": "assistant",
                    "processing_time_ms": ai_message.processing_time_ms
                },
                "updated_user": {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name,
                    "subscription_tier": user.subscription_tier,
                    "questions_used_current_cycle": user.questions_used_current_cycle,
                    "cycle_reset_time": user.cycle_reset_time.isoformat() if user.cycle_reset_time else None,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified
                } if user else None,
                "user_questions_remaining": 999999 if user else 999,
                "context_used": len(context_messages),
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            raise Exception(f"AI processing failed: {str(e)}")
        

@staticmethod
async def test_multi_agent():
   """Test if multi-agent system works"""
   if not MULTI_AGENT_AVAILABLE:
       return "Multi-agent system not available"
   
   try:
       enhanced_rag = EnhancedRAGEngine()
       
       # Simple test query
       chunks = []
       async for chunk in enhanced_rag.ask_question_with_multi_agent(
           query="ما هي حقوق الموظف؟",
           enable_trust_trail=False
       ):
           chunks.append(chunk)
       
       response = ''.join(chunks)
       return f"✅ Multi-agent test successful: {len(response)} characters generated"
       
   except Exception as e:
       return f"❌ Multi-agent test failed: {str(e)}"   
# backend/app/services/chat_service.py - Enhanced Multi-Agent Integration
# ADD this enhanced method to your existing ChatService class

@staticmethod
async def process_chat_message_enhanced(
    db: Session,
    user: Optional[User],
    conversation_id: Optional[str],
    message_content: str,
    enable_trust_trail: bool = False,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    🚀 ENHANCED: Unified chat processing with multi-agent legal reasoning
    
    Architecture:
    - Authenticated users: Multi-agent system with database persistence
    - Guests: Standard processing with session memory
    - Trust trail: Optional for conservative law firms
    - Fallback: Graceful degradation to existing system
    """
    
    start_time = datetime.utcnow()
    
    if user:
        # 🔐 AUTHENTICATED USER PATH - Multi-Agent Processing
        print(f"🤖 Processing authenticated user message with multi-agent system")
        
        # Check user limits
        can_proceed, limit_message = AuthService.check_user_limits(db, user.id)
        if not can_proceed:
            raise Exception(limit_message)
        
        # Get or create conversation
        if conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id
            ).first()
            if not conversation:
                raise Exception("Conversation not found")
        else:
            # Create new conversation
            conversation = ChatService.create_conversation(
                db, user.id, 
                title=message_content[:50] + "..." if len(message_content) > 50 else message_content
            )
            conversation_id = conversation.id
        
        # Add user message to database
        user_message = ChatService.add_message(
            db, conversation_id, "user", message_content
        )
        
        # Get conversation context from database
        context_messages = ChatService.get_conversation_context(db, conversation_id, 10)
        
        # 🧠 MULTI-AGENT PROCESSING
        try:
            if MULTI_AGENT_AVAILABLE:
                print(f"🔄 Using multi-agent legal reasoning system")
                enhanced_rag = EnhancedRAGEngine()
                
                # Collect multi-agent response with metadata
                chunks = []
                metadata = {}
                
                async def collect_multi_agent_response():
                    nonlocal metadata
                    
                    async for chunk in enhanced_rag.ask_question_with_multi_agent(
                        query=message_content,
                        conversation_context=context_messages,
                        enable_trust_trail=enable_trust_trail
                    ):
                        # Handle metadata chunks
                        if chunk.startswith("data: "):
                            try:
                                chunk_data = json.loads(chunk[6:])
                                if chunk_data.get("type") == "multi_agent_metadata":
                                    metadata.update(chunk_data)
                                elif chunk_data.get("type") == "trust_trail":
                                    metadata["trust_trail"] = chunk_data
                            except:
                                pass
                        else:
                            # Regular content chunks
                            chunks.append(chunk)
                    
                    return ''.join(chunks)
                
                ai_response = await collect_multi_agent_response()
                
                print(f"✅ Multi-agent processing successful")
                print(f"📊 Confidence: {metadata.get('overall_confidence', 0.8):.1%}")
                print(f"📚 Citations: {len(metadata.get('citations_summary', []))}")
                
            else:
                raise Exception("Multi-agent system not available")
                
        except Exception as multi_agent_error:
            print(f"⚠️ Multi-agent failed: {multi_agent_error}")
            print(f"🔄 Falling back to standard processing")
            
            # Fallback to existing single-agent processing
            try:
                from rag_engine import rag_engine
                
                chunks = []
                if context_messages and len(context_messages) > 0:
                    async for chunk in rag_engine.ask_question_with_context_streaming(message_content, context_messages):
                        chunks.append(chunk)
                else:
                    async for chunk in rag_engine.ask_question_streaming(message_content):
                        chunks.append(chunk)
                
                ai_response = ''.join(chunks)
                metadata = {"fallback_mode": True}
                
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                ai_response = "عذراً، حدث خطأ مؤقت في النظام. يرجى المحاولة مرة أخرى."
                metadata = {"error_mode": True}
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Store AI response with enhanced metadata
        ai_message = ChatService.add_message(
            db, conversation_id, "assistant", ai_response,
            confidence_score=str(metadata.get("overall_confidence", 0.8)),
            processing_time_ms=str(metadata.get("processing_time_ms", processing_time)),
            sources=json.dumps(metadata.get("citations_summary", []))
        )
        
        # Update user question count
        from app.services.user_service import UserService
        UserService.increment_question_usage(db, user.id)
        
        # 📊 ENHANCED RESPONSE WITH MULTI-AGENT DATA
        return {
            "conversation_id": conversation_id,
            "conversation_title": conversation.title,
            "user_message": {
                "id": user_message.id,
                "content": user_message.content,
                "timestamp": user_message.created_at.isoformat(),
                "role": "user"
            },
            "ai_message": {
                "id": ai_message.id,
                "content": ai_message.content,
                "timestamp": ai_message.created_at.isoformat(),
                "role": "assistant",
                "processing_time_ms": metadata.get("processing_time_ms", processing_time)
            },
            "updated_user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "subscription_tier": user.subscription_tier,
                "questions_used_current_cycle": user.questions_used_current_cycle,
                "cycle_reset_time": user.cycle_reset_time.isoformat() if user.cycle_reset_time else None,
                "is_active": user.is_active,
                "is_verified": user.is_verified
            },
            "user_questions_remaining": ChatService._get_remaining_questions(user),
            # 🔥 MULTI-AGENT SPECIFIC DATA
            "multi_agent_enabled": MULTI_AGENT_AVAILABLE and not metadata.get("fallback_mode", False),
            "overall_confidence": metadata.get("overall_confidence", 0.8),
            "citations_count": len(metadata.get("citations_summary", [])),
            "citations_summary": metadata.get("citations_summary", []),
            "trust_trail_data": metadata.get("trust_trail", {}),
            "reasoning_steps_count": metadata.get("total_steps", 0),
            "processing_mode": "multi_agent" if not metadata.get("fallback_mode") else "fallback"
        }
        
    else:
        # 🌐 GUEST USER PATH - Standard Processing
        print(f"🌐 Processing guest user message with standard system")
        
        if not session_id:
            session_id = ChatService.create_guest_session()
        
        # Add user message to session
        ChatService.add_guest_message(session_id, "user", message_content)
        
        # Get conversation context from session
        context_messages = ChatService.get_guest_context(session_id, 10)
        
        # AI processing for guests (standard system)
        try:
            from rag_engine import ask_question_with_context
            ai_response = await ask_question_with_context(
                message_content,
                context_messages
            )
            
        except Exception as e:
            ai_response = f"عذراً، حدث خطأ في النظام: {str(e)}"
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Add AI response to guest session
        ChatService.add_guest_message(session_id, "assistant", ai_response)
        
        # Create mock message objects for guests
        user_message = type('obj', (object,), {
            'id': f"guest_msg_{int(datetime.utcnow().timestamp())}",
            'content': message_content,
            'created_at': datetime.utcnow()
        })()
        
        ai_message = type('obj', (object,), {
            'id': f"guest_ai_{int(datetime.utcnow().timestamp())}",
            'content': ai_response,
            'created_at': datetime.utcnow(),
            'processing_time_ms': str(processing_time)
        })()
        
        # 📊 GUEST RESPONSE FORMAT
        return {
            "conversation_id": None,
            "session_id": session_id,
            "user_message": {
                "id": user_message.id,
                "content": user_message.content,
                "timestamp": user_message.created_at.isoformat(),
                "role": "user"
            },
            "ai_message": {
                "id": ai_message.id,
                "content": ai_message.content,
                "timestamp": ai_message.created_at.isoformat(),
                "role": "assistant",
                "processing_time_ms": ai_message.processing_time_ms
            },
            "updated_user": None,
            "user_questions_remaining": 999,
            "context_used": len(context_messages),
            "processing_time_ms": processing_time,
            # Guest users don't get multi-agent features
            "multi_agent_enabled": False,
            "processing_mode": "guest_standard"
        }
    


# Add this method to your existing ChatService class in chat_service.py

@staticmethod
async def process_chat_message_with_multi_agent(
    db: Session,
    user: Optional[User],
    conversation_id: Optional[str],
    message_content: str,
    enable_trust_trail: bool = False,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    🚀 MULTI-AGENT ENHANCED: Chat processing with legal reasoning
    
    Features:
    - Sequential legal reasoning pipeline (Analysis → Research → Arguments → Draft)
    - Trust trail for conservative law firms
    - Citation validation and confidence scoring
    - Graceful fallback to existing system
    """
    
    start_time = datetime.utcnow()
    
    if user:
        # 🔐 AUTHENTICATED USER - Multi-Agent Processing
        print(f"🤖 Multi-agent processing for user: {user.email}")
        
        # Check user limits (existing logic)
        can_proceed, limit_message = AuthService.check_user_limits(db, user.id)
        if not can_proceed:
            raise Exception(limit_message)
        
        # Get or create conversation (existing logic)
        if conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id
            ).first()
            if not conversation:
                raise Exception("Conversation not found")
        else:
            conversation = ChatService.create_conversation(
                db, user.id, 
                title=message_content[:50] + "..." if len(message_content) > 50 else message_content
            )
            conversation_id = conversation.id
        
        # Add user message to database
        user_message = ChatService.add_message(
            db, conversation_id, "user", message_content
        )
        
        # Get conversation context
        context_messages = ChatService.get_conversation_context(db, conversation_id, 10)
        
        # 🧠 MULTI-AGENT LEGAL REASONING
        try:
            from multi_agent_legal import EnhancedRAGEngine
            
            print(f"🔄 Starting multi-agent legal analysis...")
            print(f"📚 Context messages: {len(context_messages)}")
            print(f"🔍 Trust trail: {'enabled' if enable_trust_trail else 'disabled'}")
            
            enhanced_rag = EnhancedRAGEngine()
            
            # Collect multi-agent response with metadata
            chunks = []
            metadata = {
                "overall_confidence": 0.8,
                "citations_summary": [],
                "total_steps": 0,
                "processing_time_ms": 0
            }
            
            async for chunk in enhanced_rag.ask_question_with_multi_agent(
                query=message_content,
                conversation_context=context_messages,
                enable_trust_trail=enable_trust_trail
            ):
                # Parse metadata chunks
                if chunk.startswith("data: "):
                    try:
                        chunk_data = json.loads(chunk[6:])
                        if chunk_data.get("type") == "multi_agent_metadata":
                            metadata.update(chunk_data)
                        elif chunk_data.get("type") == "trust_trail":
                            metadata["trust_trail"] = chunk_data
                    except:
                        pass
                else:
                    # Regular content chunks
                    chunks.append(chunk)
            
            ai_response = ''.join(chunks)
            
            if not ai_response or ai_response.strip() == "":
                ai_response = "عذراً، لم أتمكن من معالجة سؤالك بالنظام المتقدم. يرجى إعادة المحاولة."
            
            print(f"✅ Multi-agent analysis complete!")
            print(f"📊 Confidence: {metadata.get('overall_confidence', 0.8):.1%}")
            print(f"📚 Citations: {len(metadata.get('citations_summary', []))}")
            print(f"🎯 Steps: {metadata.get('total_steps', 0)}")
            
            processing_mode = "multi_agent"
            
        except Exception as e:
            print(f"⚠️ Multi-agent failed: {e}")
            print(f"🔄 Falling back to existing system...")
            
            # Fallback to your existing enhanced RAG
            try:
                from rag_engine import rag_engine
                
                chunks = []
                if context_messages and len(context_messages) > 0:
                    async for chunk in rag_engine.ask_question_with_context_streaming(message_content, context_messages):
                        chunks.append(chunk)
                else:
                    async for chunk in rag_engine.ask_question_streaming(message_content):
                        chunks.append(chunk)
                
                ai_response = ''.join(chunks)
                metadata = {"fallback_used": True}
                processing_mode = "fallback_enhanced"
                
                print(f"✅ Fallback processing successful")
                
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")
                ai_response = "عذراً، حدث خطأ مؤقت في النظام. يرجى المحاولة مرة أخرى."
                metadata = {"error_mode": True}
                processing_mode = "error"
        
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Store AI response with enhanced metadata
        ai_message = ChatService.add_message(
            db, conversation_id, "assistant", ai_response,
            confidence_score=str(metadata.get("overall_confidence", 0.8)),
            processing_time_ms=str(metadata.get("processing_time_ms", processing_time)),
            sources=json.dumps(metadata.get("citations_summary", []))
        )
        
        # Update user question count
        from app.services.user_service import UserService
        UserService.increment_question_usage(db, user.id)
        
        # Return enhanced response
        return {
            "conversation_id": conversation_id,
            "conversation_title": conversation.title,
            "user_message": {
                "id": user_message.id,
                "content": user_message.content,
                "timestamp": user_message.created_at.isoformat(),
                "role": "user"
            },
            "ai_message": {
                "id": ai_message.id,
                "content": ai_response,
                "timestamp": ai_message.created_at.isoformat(),
                "role": "assistant",
                "processing_time_ms": metadata.get("processing_time_ms", processing_time)
            },
            "updated_user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "subscription_tier": user.subscription_tier,
                "questions_used_current_cycle": user.questions_used_current_cycle,
                "cycle_reset_time": user.cycle_reset_time.isoformat() if user.cycle_reset_time else None,
                "is_active": user.is_active,
                "is_verified": user.is_verified
            },
            "user_questions_remaining": ChatService._get_remaining_questions(user),
            # 🔥 MULTI-AGENT METADATA
            "multi_agent_enabled": processing_mode == "multi_agent",
            "processing_mode": processing_mode,
            "overall_confidence": metadata.get("overall_confidence", 0.8),
            "citations_count": len(metadata.get("citations_summary", [])),
            "citations_summary": metadata.get("citations_summary", []),
            "reasoning_steps_count": metadata.get("total_steps", 0),
            "trust_trail_data": metadata.get("trust_trail", {}),
            "trust_trail_enabled": enable_trust_trail
        }
        
    else:
        # 🌐 GUEST USER - Standard Processing (unchanged)
        print(f"🌐 Standard processing for guest: {session_id}")
        
        # Use your existing guest processing logic
        return await ChatService.process_unified_message(
            db=db,
            user=None,
            message_content=message_content,
            conversation_id=None,
            session_id=session_id
        )        


