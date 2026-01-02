"""
Pydantic schemas for User models
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date


class UserBase(BaseModel):
    """Base user schema"""
    name: str
    email: EmailStr
    role: str
    team_id: Optional[int] = None
    onboarding_date: Optional[date] = None
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a user"""
    pass


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    team_id: Optional[int] = None
    onboarding_date: Optional[date] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    
    class Config:
        from_attributes = True

