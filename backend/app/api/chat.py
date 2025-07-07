"""
Fixed Chat API endpoints with proper JWT authentication.
Replace your entire backend/app/api/chat.py with this version.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Form, Query
from sqlalchemy.orm import Session
from app.database import get_database
from app.dependencies.simple_auth import get_current_active_user, get_optional_current_user
from app.services.chat_service import ChatService
from app.services.cooldown_service import CooldownService
from app.services.guest_service import GuestService
from app.models.user import User
from app.models.conversation import Conversation, Message

router = APIRouter(prefix="/chat", tags=["chat"])


def _calculate_questions_remaining(user: User) -> int:
    """Calculate remaining questions for user based on subscription."""
    if user.subscription_tier == "free":
        return 999999
    elif user.subscription_tier == "pro":
        return 999999
    else:  # enterprise
        return 999999


@router.post("/message")
async def send_chat_message(
    message: str = Form(..., description="User message"),
    conversation_id: Optional[str] = Form(None, description="Existing conversation ID (optional)"),
    session_id: Optional[str] = Form(None, description="Guest session ID (for guests only)"),
    db: Session = Depends(get_database),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Send a message in a unified chat system for both guests and signed-in users."""
    try:
        # ✅ UNIFIED: Handle both guests and signed-in users
        if current_user:
            # Signed-in user flow
            user_type = "signed_in"
            user_identifier = current_user.email
            
            # Check cooldown for signed-in users
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
            
            # Use question for signed-in user
            if not CooldownService.use_question(db, current_user):
                raise HTTPException(status_code=500, detail="Failed to process question")
            
            print(f"🔍 DEBUG: Signed-in user {current_user.email}: cycle questions {current_user.questions_used_current_cycle}")
            
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
            
            guest_session = GuestService.get_guest_session(session_id)
            print(f"🔍 DEBUG: Guest user {session_id}: questions used {guest_session['questions_used']}")
        
        print(f"🔍 DEBUG: Received message from {user_identifier}: {message}")
        print(f"🔍 DEBUG: Conversation ID: {conversation_id}")
        
        # ✅ UNIFIED: Process chat message (works for both guests and signed-in)
        result = await ChatService.process_chat_message(
            db=db,
            user=current_user,  # None for guests, User object for signed-in
            conversation_id=conversation_id,
            message_content=message.strip()
        )
        
        # ✅ UNIFIED: Get updated status for response
        if current_user:
            # Refresh user data after processing
            db.refresh(current_user)
            cooldown_status = CooldownService.get_question_status(db, current_user)
            
            result["updated_user"] = {
    "id": current_user.id,
    "email": current_user.email,
    "full_name": current_user.full_name,
    "is_active": current_user.is_active,
    "subscription_tier": current_user.subscription_tier,
    "questions_used_this_month": current_user.questions_used_this_month,
    "questions_used_current_cycle": current_user.questions_used_current_cycle,
    "cycle_reset_time": current_user.cycle_reset_time.isoformat() if current_user.cycle_reset_time else None,
    "is_verified": current_user.is_verified,
    "questions_remaining": _calculate_questions_remaining(current_user)
}
        else:
            # Guest status
            guest_session = GuestService.get_guest_session(session_id)
            cooldown_status = {
                "questions_available": CooldownService.GUEST_QUESTION_LIMIT - guest_session["questions_used"],
                "questions_used": guest_session["questions_used"],
                "max_questions": CooldownService.GUEST_QUESTION_LIMIT,
                "reset_time": guest_session["reset_time"].isoformat() if guest_session["reset_time"] else None,
                "can_ask_question": (CooldownService.GUEST_QUESTION_LIMIT - guest_session["questions_used"]) > 0
            }
        
        # ✅ UNIFIED: Add cooldown status to response
        result["cooldown_status"] = cooldown_status
        result["user_type"] = user_type
        
        print(f"✅ DEBUG: Message processed for {user_identifier}")
        return result
        
    except HTTPException:
        # Re-raise cooldown errors as-is
        raise
    except Exception as e:
        # ✅ UNIFIED: Rollback question usage on error
        if current_user:
            current_user.questions_used_current_cycle -= 1
            if current_user.questions_used_current_cycle <= 0:
                current_user.cycle_reset_time = None
            db.commit()
        elif session_id:
            guest_session = GuestService.get_guest_session(session_id)
            guest_session["questions_used"] -= 1
        
        print(f"❌ DEBUG: Exception for {user_identifier}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/conversations")
async def get_user_conversations(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)  # ✅ REAL JWT AUTH
):
    """Get user's conversation list with pagination."""
    
    print(f"🔍 DEBUG: Loading conversations for user: {current_user.email}")
    
    conversations = ChatService.get_user_conversations(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    print(f"🔍 DEBUG: Found {len(conversations)} conversations for {current_user.email}")
    
    # Format response with conversation previews
    conversation_list = []
    for conv in conversations:
        # Get last message for preview
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
        "limit": limit,
        "offset": offset,
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


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)  # ✅ REAL JWT AUTH
):
    """Get all messages in a conversation."""
    
    print(f"🔍 DEBUG: Loading messages for conversation: {conversation_id} (user: {current_user.email})")
    
    # Verify conversation belongs to current user
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        print(f"❌ DEBUG: Conversation {conversation_id} not found for user {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = ChatService.get_conversation_messages(db, conversation_id, limit)
    print(f"✅ DEBUG: Found {len(messages)} messages for user {current_user.email}")
    
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


@router.delete("/conversations/{conversation_id}")
async def archive_conversation(
    conversation_id: str,
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)  # ✅ REAL JWT AUTH
):
    """Archive (soft delete) a conversation."""
    
    print(f"🔍 DEBUG: Deleting conversation: {conversation_id} (user: {current_user.email})")
    
    success = ChatService.archive_conversation(db, conversation_id, current_user.id)
    
    if not success:
        print(f"❌ DEBUG: Failed to delete conversation {conversation_id} for user {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    print(f"✅ DEBUG: Conversation deleted successfully for user {current_user.email}")
    
    return {
        "message": "Conversation archived successfully",
        "conversation_id": conversation_id
    }


@router.put("/conversations/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str,
    new_title: str = Form(...),
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)  # ✅ REAL JWT AUTH
):
    """Update conversation title."""
    
    print(f"🔍 DEBUG: Updating title for conversation: {conversation_id} (user: {current_user.email})")
    print(f"🔍 DEBUG: New title: {new_title}")
    
    # Verify conversation belongs to current user
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        print(f"❌ DEBUG: Conversation {conversation_id} not found for user {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    updated_conversation = ChatService.update_conversation_title(
        db, conversation_id, new_title.strip()
    )
    
    print(f"✅ DEBUG: Title updated successfully for user {current_user.email}")
    
    return {
        "conversation_id": conversation_id,
        "new_title": updated_conversation.title,
        "updated_at": updated_conversation.updated_at.isoformat()
    }


@router.get("/stats")
async def get_chat_stats(
    db: Session = Depends(get_database),
    current_user: User = Depends(get_current_active_user)  # ✅ REAL JWT AUTH
):
    """Get user's chat statistics with updated data."""
    
    print(f"🔍 DEBUG: Getting stats for user: {current_user.email}")
    
    conversations = ChatService.get_user_conversations(db, current_user.id, limit=1000)
    
    total_conversations = len(conversations)
    total_messages = 0
    
    for conv in conversations:
        messages = ChatService.get_conversation_messages(db, conv.id)
        total_messages += len(messages)
    
    print(f"✅ DEBUG: Stats calculated for user {current_user.email}: {total_conversations} conversations, {total_messages} messages")
    
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "questions_used_this_month": current_user.questions_used_this_month,
        "subscription_tier": current_user.subscription_tier,
        "questions_remaining": _calculate_questions_remaining(current_user)
    }


@router.get("/status")
async def get_cooldown_status(
    session_id: Optional[str] = Query(None),
    db: Session = Depends(get_database),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """Get current cooldown status for both guests and signed-in users."""
    
    if current_user:
        # Signed-in user status
        status = CooldownService.get_question_status(db, current_user)
        status["user_type"] = "signed_in"
        return status
    elif session_id:
        # Guest user status
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session ID required for guest users"
        )