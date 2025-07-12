# backend/app/api/chat.py - Unified Chat API for All Users

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Form, Query
from sqlalchemy.orm import Session
from app.database import get_database
from app.dependencies.simple_auth import get_current_active_user, get_optional_current_user
from app.services.chat_service import ChatService
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
async def send_unified_message(
    message: str = Form(..., description="User message"),
    conversation_id: Optional[str] = Form(None, description="Existing conversation ID (for authenticated users)"),
    session_id: Optional[str] = Form(None, description="Session ID (for guests)"),
    db: Session = Depends(get_database),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    🔥 UNIFIED: Send message endpoint for both guests and authenticated users
    
    - Authenticated users: Uses database-persistent conversations
    - Guests: Uses in-memory session-based conversations with context
    """
    try:
        print(f"🔄 Processing unified message from {'user' if current_user else 'guest'}: {message[:50]}...")
        
        # Process message through unified service
        result = await ChatService.process_unified_message(
            db=db,
            user=current_user,
            message_content=message.strip(),
            conversation_id=conversation_id,
            session_id=session_id
        )
        
        print(f"✅ Message processed successfully for {'user' if current_user else 'guest'}")
        return result
        
    except Exception as e:
        print(f"❌ Error processing message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )

@router.get("/conversations")
async def get_user_conversations(
    limit: int = Query(50, description="Maximum number of conversations to return"),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get all conversations for authenticated user (not available for guests)."""
    try:
        conversations = ChatService.get_user_conversations(db, current_user.id, limit)
        
        conversation_list = []
        for conv in conversations:
            # Get latest message for preview
            latest_message = db.query(Message).filter(
                Message.conversation_id == conv.id
            ).order_by(Message.created_at.desc()).first()
            
            conversation_list.append({
                "id": conv.id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "latest_message": latest_message.content[:100] + "..." if latest_message and len(latest_message.content) > 100 else latest_message.content if latest_message else "",
                "message_count": db.query(Message).filter(Message.conversation_id == conv.id).count()
            })
        
        return {
            "conversations": conversation_list,
            "total_count": len(conversation_list),
            "user_info": {
                "id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "subscription_tier": current_user.subscription_tier,
                "questions_remaining": _calculate_questions_remaining(current_user)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch conversations: {str(e)}"
        )

@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = Query(100, description="Maximum number of messages to return"),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Get messages from a specific conversation (authenticated users only)."""
    try:
        print(f"🔍 Loading messages for conversation: {conversation_id} (user: {current_user.email})")
        
        # Verify conversation belongs to current user
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            print(f"❌ Conversation {conversation_id} not found for user {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        messages = ChatService.get_conversation_messages(db, conversation_id, limit)
        print(f"✅ Found {len(messages)} messages for user {current_user.email}")
        
        # Format messages for frontend
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
            "total_messages": len(message_list),
            "current_user": {
                "id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.full_name,
                "subscription_tier": current_user.subscription_tier,
                "questions_used_this_month": current_user.questions_used_this_month,
                "questions_used_current_cycle": current_user.questions_used_current_cycle,
                "cycle_reset_time": current_user.cycle_reset_time.isoformat() if current_user.cycle_reset_time else None,
                "is_active": current_user.is_active,
                "is_verified": current_user.is_verified,
                "questions_remaining": _calculate_questions_remaining(current_user)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch messages: {str(e)}"
        )

@router.put("/conversations/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str,
    new_title: str = Form(..., description="New conversation title"),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Update conversation title (authenticated users only)."""
    try:
        # Verify conversation belongs to user
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        updated_conversation = ChatService.update_conversation_title(
            db, conversation_id, new_title.strip()
        )
        
        return {
            "conversation_id": conversation_id,
            "new_title": updated_conversation.title,
            "updated_at": updated_conversation.updated_at.isoformat(),
            "success": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update title: {str(e)}"
        )

@router.delete("/conversations/{conversation_id}")
async def archive_conversation(
    conversation_id: str,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)
):
    """Archive (soft delete) a conversation (authenticated users only)."""
    try:
        success = ChatService.archive_conversation(db, conversation_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return {
            "conversation_id": conversation_id,
            "archived": True,
            "message": "Conversation archived successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to archive conversation: {str(e)}"
        )

@router.get("/status")
async def get_chat_status(
    db: Session = Depends(get_database),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get current chat status for both guests and authenticated users."""
    try:
        if current_user:
            # Authenticated user status
            conversations_count = db.query(Conversation).filter(
                Conversation.user_id == current_user.id,
                Conversation.is_active == True
            ).count()
            
            return {
                "user_type": "authenticated",
                "user_info": {
                    "id": current_user.id,
                    "email": current_user.email,
                    "full_name": current_user.full_name,
                    "subscription_tier": current_user.subscription_tier,
                    "questions_used_current_cycle": current_user.questions_used_current_cycle,
                    "questions_remaining": _calculate_questions_remaining(current_user),
                    "conversations_count": conversations_count
                },
                "features": {
                    "persistent_conversations": True,
                    "conversation_history": True,
                    "export_functionality": True,
                    "unlimited_questions": current_user.subscription_tier != "free"
                }
            }
        else:
            # Guest user status
            return {
                "user_type": "guest",
                "session_info": {
                    "session_based": True,
                    "context_memory": True,
                    "questions_remaining": 999
                },
                "features": {
                    "persistent_conversations": False,
                    "conversation_history": False,
                    "export_functionality": False,
                    "unlimited_questions": False
                }
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )

# 🔥 NEW: Guest session management endpoints
@router.post("/guest/session")
async def create_guest_session():
    """Create a new guest session for conversation context."""
    try:
        session_id = ChatService.create_guest_session()
        return {
            "session_id": session_id,
            "message": "Guest session created successfully",
            "features": {
                "context_memory": True,
                "session_based": True,
                "max_messages": 20
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create guest session: {str(e)}"
        )

@router.get("/guest/session/{session_id}/context")
async def get_guest_session_context(session_id: str):
    """Get conversation context for a guest session."""
    try:
        context = ChatService.get_guest_context(session_id, 10)
        return {
            "session_id": session_id,
            "context_messages": context,
            "message_count": len(context),
            "context_available": len(context) > 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session context: {str(e)}"
        )