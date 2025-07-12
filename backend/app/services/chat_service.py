# backend/app/services/chat_service.py - Enhanced for Guest Support

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import json

from app.models.conversation import Conversation, Message
from app.models.user import User
from app.services.auth_service import AuthService
from rag_engine import ask_question_with_context

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
        try:
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
                AuthService.increment_user_questions(db, user.id)
                
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