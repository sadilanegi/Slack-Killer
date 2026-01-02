"""
User model for engineers, managers, and admins
"""
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    """User model representing engineers, managers, and admins"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    role = Column(String, nullable=False, index=True)  # backend, frontend, devops, manager, admin
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, index=True)
    onboarding_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    activity_events = relationship("ActivityEvent", back_populates="user")
    weekly_metrics = relationship("WeeklyUserMetrics", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, role={self.role})>"


class Team(Base):
    """Team model for grouping users"""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    
    # Relationships
    users = relationship("User", backref="team")

