"""
Weekly user metrics model for aggregated productivity data
"""
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base


class WeeklyUserMetrics(Base):
    """Weekly aggregated metrics per user"""
    __tablename__ = "weekly_user_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    week_start = Column(Date, nullable=False, index=True)
    
    # Activity metrics
    tickets_completed = Column(Integer, default=0, nullable=False)
    story_points = Column(Float, default=0.0, nullable=False)
    prs_authored = Column(Integer, default=0, nullable=False)
    prs_reviewed = Column(Integer, default=0, nullable=False)
    commits = Column(Integer, default=0, nullable=False)
    docs_authored = Column(Integer, default=0, nullable=False)
    meeting_hours = Column(Float, default=0.0, nullable=False)
    
    # Calculated metrics
    composite_score = Column(Float, nullable=True)  # 0-100 score
    baseline_score = Column(Float, nullable=True)  # User's historical baseline
    engagement_status = Column(String, nullable=True, index=True)  # healthy, watch, needs_review
    
    # Additional flags and context
    flags = Column(JSONB, nullable=True)  # PTO, onboarding, role_change, on_call, etc.
    
    # Relationships
    user = relationship("User", back_populates="weekly_metrics")
    
    # Composite unique constraint and index
    __table_args__ = (
        Index('idx_user_week_start', 'user_id', 'week_start', unique=True),
        Index('idx_week_start', 'week_start'),
    )
    
    def __repr__(self):
        return f"<WeeklyUserMetrics(user_id={self.user_id}, week_start={self.week_start}, status={self.engagement_status})>"

