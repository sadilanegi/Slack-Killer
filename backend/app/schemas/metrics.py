"""
Pydantic schemas for metrics and reports
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import date, datetime


class WeeklyMetricsBase(BaseModel):
    """Base weekly metrics schema"""
    week_start: date
    tickets_completed: int = 0
    story_points: float = 0.0
    prs_authored: int = 0
    prs_reviewed: int = 0
    commits: int = 0
    docs_authored: int = 0
    meeting_hours: float = 0.0
    composite_score: Optional[float] = None
    baseline_score: Optional[float] = None
    engagement_status: Optional[str] = None
    flags: Optional[Dict[str, Any]] = None


class WeeklyMetricsResponse(WeeklyMetricsBase):
    """Weekly metrics response schema"""
    id: int
    user_id: int
    
    class Config:
        from_attributes = True


class UserMetricsSummary(BaseModel):
    """Summary of user metrics over time"""
    user_id: int
    user_name: str
    user_role: str
    current_week: WeeklyMetricsResponse
    previous_weeks: List[WeeklyMetricsResponse]
    trend: str  # improving, stable, declining
    engagement_status: str


class TeamSummary(BaseModel):
    """Team-level summary"""
    team_id: int
    team_name: str
    total_members: int
    healthy_count: int
    watch_count: int
    needs_review_count: int
    average_composite_score: float
    members: List[UserMetricsSummary]


class WeeklyReport(BaseModel):
    """Weekly report for all teams"""
    week_start: date
    generated_at: datetime
    teams: List[TeamSummary]
    total_users: int
    healthy_users: int
    watch_users: int
    needs_review_users: int


class OverrideRequest(BaseModel):
    """Request to override engagement status"""
    user_id: int
    week_start: date
    reason: str
    flags: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class OverrideResponse(BaseModel):
    """Response for override creation"""
    id: int
    user_id: int
    week_start: date
    reason: str
    created_at: datetime
    
    class Config:
        from_attributes = True

