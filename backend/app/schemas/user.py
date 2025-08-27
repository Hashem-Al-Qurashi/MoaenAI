"""
User schemas for API validation.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    is_active: bool = Field(True, description="Whether the user account is active")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=100, description="User password (8-100 characters)")
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "Ahmed Mohammed",
                "password": "securepassword123",
                "is_active": True
            }
        }


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    full_name: Optional[str] = Field(None, description="Updated full name")
    email: Optional[EmailStr] = Field(None, description="Updated email address")
    is_active: Optional[bool] = Field(None, description="Updated active status")
    
    class Config:
        schema_extra = {
            "example": {
                "full_name": "Ahmed Mohammed Al-Saud",
                "email": "ahmed.new@example.com"
            }
        }


class User(UserBase):
    """Schema for user response (without sensitive data)"""
    id: str = Field(..., description="User unique identifier")
    subscription_tier: str = Field("free", description="User subscription tier")
    questions_used_this_month: int = Field(0, description="Number of questions used this month")
    is_verified: bool = Field(False, description="Whether the user email is verified")
    
    class Config:
        orm_mode = True  # Allows conversion from SQLAlchemy models
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "full_name": "Ahmed Mohammed",
                "is_active": True,
                "subscription_tier": "free",
                "questions_used_this_month": 5,
                "is_verified": True
            }
        }


class UserInDB(User):
    """Schema for user in database (includes sensitive data)"""
    hashed_password: str = Field(..., description="Hashed password")
    
    class Config:
        orm_mode = True