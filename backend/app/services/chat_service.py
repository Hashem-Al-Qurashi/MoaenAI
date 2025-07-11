# File: backend/app/services/chat_service.py
# ✅ FIXED: ChatService now handles both guests and authenticated users

"""
Chat service for managing conversations and messages.
Fixed to use Enhanced RAG Engine with OpenAI + Saudi Legal Templates
SUPPORTS BOTH GUESTS AND AUTHENTICATED USERS
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import asyncio

from app.models.conversation import Conversation, Message
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.user_service import UserService


class ChatService:
    """Service for chat conversation management - supports guests and auth users"""

    @staticmethod
    def create_conversation(db: Session, user_id: str, title: Optional[str] = None) -> Conversation:
        """Create a new conversation for a user"""
        conversation = Conversation(
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
        limit: int = 20, 
        offset: int = 0
    ) -> List[Conversation]:
        """Get user's conversations with pagination"""
        return db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_active == True
        ).order_by(
            Conversation.updated_at.desc()
        ).offset(offset).limit(limit).all()

    @staticmethod
    def get_conversation_messages(
        db: Session, 
        conversation_id: str, 
        limit: int = 50
    ) -> List[Message]:
        """Get messages in a conversation"""
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at.asc()
        ).limit(limit).all()

    @staticmethod
    def add_message_to_conversation(
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
        """Get recent conversation context for AI"""
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

    @staticmethod
    async def process_chat_message(
        db: Session,
        user: Optional[User],  # ✅ FIXED: Now Optional[User] to handle guests
        conversation_id: Optional[str],
        message_content: str,
        session_id: Optional[str] = None  # ✅ NEW: For guest session tracking
    ) -> Dict[str, Any]:
        """
        Process a chat message with context from conversation history
        Using Enhanced RAG Engine with OpenAI + Saudi Legal Templates
        ✅ SUPPORTS BOTH GUESTS AND AUTHENTICATED USERS
        """
        
        # ✅ HANDLE: Different logic for guests vs authenticated users
        if user:
            # ✅ AUTHENTICATED USER PATH
            print(f"🔐 Processing message for authenticated user: {user.email}")
            
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
            
            # Add user message to database
            user_message = ChatService.add_message_to_conversation(
                db, conversation.id, "user", message_content
            )
            
            # Get conversation context for AI
            context = ChatService.get_conversation_context(db, conversation.id)
            
        else:
            # ✅ GUEST USER PATH
            print(f"👤 Processing message for guest user: {session_id}")
            
            # ✅ GUEST: No database storage, use in-memory context
            conversation = None
            user_message = None
            
            # ✅ GUEST: Build context from session (if available)
            # For now, no persistent context for guests until page refresh
            context = []  # Could be enhanced later with sessionStorage
        
        # ✅ UNIFIED: Process with Enhanced RAG Engine (same for both)
        start_time = datetime.now()
        try:
            # Import the Enhanced RAG engine
            from rag_engine import rag_engine   
            
            print(f"🤖 Processing with Enhanced RAG: {message_content[:50]}...")
            print(f"📚 Context messages: {len(context)}")
            
            # Convert to async and collect streaming response
            chunks = []
            async def collect_response():
                try:
                    if context and len(context) > 0:  # If there's conversation history
                        print("🔄 Using context-aware processing...")
                        async for chunk in rag_engine.ask_question_with_context_streaming(message_content, context):
                            chunks.append(chunk)
                    else:  # First message in conversation
                        print("🔄 Using standard processing...")
                        async for chunk in rag_engine.ask_question_streaming(message_content):
                            chunks.append(chunk)
                    return ''.join(chunks)
                except Exception as stream_error:
                    print(f"❌ Streaming error: {stream_error}")
                    raise stream_error
            
            # Run the async function
            ai_response = await collect_response()
            
            if not ai_response or ai_response.strip() == "":
                ai_response = "عذراً، لم أتمكن من معالجة سؤالك. يرجى إعادة صياغة السؤال."
            
            print(f"✅ Enhanced RAG response generated: {len(ai_response)} characters")
            
        except Exception as e:
            print(f"❌ Enhanced RAG failed: {e}")
            # Fallback response with helpful message
            ai_response = f"""عذراً، حدث خطأ مؤقت في النظام.

يرجى المحاولة مرة أخرى، أو إعادة صياغة السؤال بطريقة أخرى.

إذا استمر الخطأ، يمكنك التواصل مع الدعم الفني."""

        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # ✅ HANDLE: Different response structure for guests vs authenticated
        if user and conversation:
            # ✅ AUTHENTICATED: Save to database
            ai_message = ChatService.add_message_to_conversation(
                db, conversation.id, "assistant", ai_response,
                confidence_score="high",
                processing_time_ms=str(processing_time)
            )
            
            # Increment user's question usage
            UserService.increment_question_usage(db, user.id)
            
            return {
                "conversation_id": conversation.id,
                "conversation_title": conversation.title,
                "user_message": {
                    "id": user_message.id,
                    "content": user_message.content,
                    "timestamp": user_message.created_at.isoformat()
                },
                "ai_message": {
                    "id": ai_message.id,
                    "content": ai_message.content,
                    "timestamp": ai_message.created_at.isoformat(),
                    "processing_time_ms": processing_time
                },
                "user_questions_remaining": ChatService._get_remaining_questions(user)
            }
        else:
            # ✅ GUEST: Return in-memory response
            return {
                "conversation_id": session_id,  # Use session_id as temp conversation_id
                "conversation_title": "محادثة ضيف",
                "user_message": {
                    "id": f"guest_user_{int(datetime.now().timestamp())}",
                    "content": message_content,
                    "timestamp": datetime.now().isoformat()
                },
                "ai_message": {
                    "id": f"guest_ai_{int(datetime.now().timestamp())}",
                    "content": ai_response,
                    "timestamp": datetime.now().isoformat(),
                    "processing_time_ms": processing_time
                },
                "user_questions_remaining": 999  # Guests have unlimited (with cooldown)
            }
    
    @staticmethod
    def _get_remaining_questions(user: User) -> int:
        """Calculate remaining questions for user based on subscription."""
        if user.subscription_tier == "free":
            return max(0, 3 - user.questions_used_this_month)
        elif user.subscription_tier == "pro":
            return max(0, 100 - user.questions_used_this_month)
        else:  # enterprise
            return 999999  # "unlimited"