"""
User management service for CRUD operations.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash


class UserService:
    """Service for user management operations"""

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email address"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> Optional[User]:
        """
        Create a new user account.
        
        Args:
            db: Database session
            user_create: User creation data
            
        Returns:
            Created user or None if email already exists
        """
        try:
            # Check if user already exists
            existing_user = UserService.get_user_by_email(db, user_create.email)
            if existing_user:
                return None
            
            # Hash the password
            hashed_password = get_password_hash(user_create.password)
            
            # Create user instance
            db_user = User(
                email=user_create.email,
                hashed_password=hashed_password,
                full_name=user_create.full_name,
                is_active=user_create.is_active,
                is_verified=False,  # Email verification required
                subscription_tier="free",
                questions_used_this_month=0
            )
            
            # Save to database
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            return db_user
            
        except IntegrityError:
            db.rollback()
            return None

    @staticmethod
    def update_user(db: Session, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """
        Update user information.
        
        Args:
            db: Database session
            user_id: User ID to update
            user_update: Updated user data
            
        Returns:
            Updated user or None if not found
        """
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            return None
        
        # Update fields if provided
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        try:
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError:
            db.rollback()
            return None

    @staticmethod
    def increment_question_usage(db: Session, user_id: str) -> bool:
        """
        Increment user's monthly question usage.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            return False
        
        db_user.questions_used_this_month += 1
        
        try:
            db.commit()
            return True
        except:
            db.rollback()
            return False

    @staticmethod
    def reset_monthly_usage(db: Session) -> int:
        """
        Reset monthly question usage for all users.
        
        Args:
            db: Database session
            
        Returns:
            Number of users updated
        """
        try:
            updated_count = db.query(User).update({
                User.questions_used_this_month: 0
            })
            db.commit()
            return updated_count
        except:
            db.rollback()
            return 0

    @staticmethod
    def get_user_stats(db: Session, user_id: str) -> Optional[dict]:
        """
        Get user statistics.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User statistics dictionary
        """
        db_user = UserService.get_user_by_id(db, user_id)
        if not db_user:
            return None
        
        # Get consultation count
        from app.models.consultation import Consultation
        consultation_count = db.query(Consultation).filter(
            Consultation.user_id == user_id
        ).count()
        
        return {
            "user_id": user_id,
            "total_consultations": consultation_count,
            "questions_this_month": db_user.questions_used_this_month,
            "subscription_tier": db_user.subscription_tier,
            "member_since": db_user.created_at.isoformat(),
            "is_verified": db_user.is_verified
        }