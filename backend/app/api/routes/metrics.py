"""
Metrics API routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from app.core.database import get_db
from app.core.security import get_current_user, check_permission
from app.models.user import User
from app.models.weekly_metrics import WeeklyUserMetrics
from app.schemas.metrics import (
    WeeklyMetricsResponse,
    UserMetricsSummary,
    TeamSummary
)
from app.services.metrics_service import MetricsService
from app.services.slack_detection import EngagementDetectionService
from app.utils.time import get_week_start, get_weeks_ago

router = APIRouter()
metrics_service = MetricsService()
engagement_service = EngagementDetectionService()


@router.get("/users/{user_id}", response_model=UserMetricsSummary)
async def get_user_metrics(
    user_id: int,
    weeks: int = Query(default=8, ge=1, le=52),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get metrics summary for a user"""
    if not check_permission(current_user, target_user_id=user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's metrics"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get current week
    current_week_start = get_week_start(datetime.utcnow()).date()
    current_week_metrics = db.query(WeeklyUserMetrics).filter(
        WeeklyUserMetrics.user_id == user_id,
        WeeklyUserMetrics.week_start == current_week_start
    ).first()
    
    if not current_week_metrics:
        # Aggregate if not exists
        current_week_metrics = metrics_service.aggregate_week(db, user_id, current_week_start)
        engagement_service.update_engagement_status(db, user_id, current_week_start)
        db.refresh(current_week_metrics)
    
    # Get previous weeks
    cutoff_date = get_weeks_ago(weeks)
    previous_weeks = db.query(WeeklyUserMetrics).filter(
        WeeklyUserMetrics.user_id == user_id,
        WeeklyUserMetrics.week_start >= cutoff_date.date(),
        WeeklyUserMetrics.week_start < current_week_start
    ).order_by(WeeklyUserMetrics.week_start.desc()).all()
    
    # Calculate trend
    if len(previous_weeks) >= 2:
        recent_scores = [wm.composite_score for wm in previous_weeks[:4] if wm.composite_score]
        if len(recent_scores) >= 2:
            avg_recent = sum(recent_scores) / len(recent_scores)
            if current_week_metrics.composite_score:
                if current_week_metrics.composite_score > avg_recent * 1.1:
                    trend = "improving"
                elif current_week_metrics.composite_score < avg_recent * 0.9:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "stable"
        else:
            trend = "stable"
    else:
        trend = "stable"
    
    return UserMetricsSummary(
        user_id=user.id,
        user_name=user.name,
        user_role=user.role,
        current_week=current_week_metrics,
        previous_weeks=previous_weeks,
        trend=trend,
        engagement_status=current_week_metrics.engagement_status or "healthy"
    )


@router.get("/users/{user_id}/weekly", response_model=List[WeeklyMetricsResponse])
async def get_user_weekly_metrics(
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weekly metrics for a user over a date range"""
    if not check_permission(current_user, target_user_id=user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's metrics"
        )
    
    query = db.query(WeeklyUserMetrics).filter(WeeklyUserMetrics.user_id == user_id)
    
    if start_date:
        query = query.filter(WeeklyUserMetrics.week_start >= start_date)
    if end_date:
        query = query.filter(WeeklyUserMetrics.week_start <= end_date)
    
    return query.order_by(WeeklyUserMetrics.week_start.desc()).all()

