"""
Security utilities for authentication and authorization
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    # Ensure 'sub' is a string (python-jose requirement)
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        # Convert string back to int for database query
        user_id = int(user_id_str)
    except (JWTError, ValueError) as e:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        print(f"DEBUG: User not found for ID: {user_id}")
        raise credentials_exception
    return user


def check_permission(user: User, target_user_id: Optional[int] = None, target_team_id: Optional[int] = None) -> bool:
    """
    Check if user has permission to access resource
    
    Rules:
    - Admin: can access all
    - Manager: can access their team
    - Engineer: can only access themselves
    """
    if user.role == "admin":
        return True
    
    if user.role == "manager":
        if target_team_id and user.team_id == target_team_id:
            return True
        if target_user_id:
            # Check if target user is in manager's team
            db = next(get_db())
            target_user = db.query(User).filter(User.id == target_user_id).first()
            if target_user and target_user.team_id == user.team_id:
                return True
    
    if user.role in ["backend", "frontend", "devops"]:
        if target_user_id and user.id == target_user_id:
            return True
    
    return False

