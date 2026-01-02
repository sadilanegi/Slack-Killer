"""
Activity event model for tracking individual activities
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base


class ActivityEvent(Base):
    """Activity event model for tracking individual activities from various sources"""
    __tablename__ = "activity_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    source = Column(String, nullable=False, index=True)  # jira, github, docs, calendar
    event_type = Column(String, nullable=False)  # ticket_completed, pr_opened, pr_merged, pr_reviewed, commit, doc_created, meeting
    occurred_at = Column(DateTime, nullable=False, index=True)
    event_metadata = Column(JSONB, nullable=True)  # Flexible JSON storage for source-specific data (renamed from 'metadata' to avoid SQLAlchemy conflict)
    
    # Relationships
    user = relationship("User", back_populates="activity_events")
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('idx_user_occurred_at', 'user_id', 'occurred_at'),
    )
    
    def __repr__(self):
        return f"<ActivityEvent(id={self.id}, user_id={self.user_id}, source={self.source}, event_type={self.event_type})>"

