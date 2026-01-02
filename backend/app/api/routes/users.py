"""
User management API routes
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, check_permission
from app.models.user import User
from app.schemas.user import UserResponse, UserCreate, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user by ID (with permission check)"""
    if not check_permission(current_user, target_user_id=user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.get("/", response_model=List[UserResponse])
async def list_users(
    team_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List users (filtered by permissions)"""
    query = db.query(User).filter(User.is_active == True)
    
    # Apply permission filters
    if current_user.role == "admin":
        # Admin can see all
        pass
    elif current_user.role == "manager":
        # Manager can see their team
        query = query.filter(User.team_id == current_user.team_id)
    else:
        # Engineers can only see themselves
        query = query.filter(User.id == current_user.id)
    
    if team_id:
        if not check_permission(current_user, target_team_id=team_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this team"
            )
        query = query.filter(User.team_id == team_id)
    
    return query.all()

