"""
Reports API routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import get_current_user, check_permission
from app.models.user import User, Team
from app.models.weekly_metrics import WeeklyUserMetrics
from app.schemas.metrics import TeamSummary, WeeklyReport, UserMetricsSummary
from app.services.metrics_service import MetricsService
from app.services.slack_detection import EngagementDetectionService
from app.utils.time import get_week_start
from app.api.routes.metrics import get_user_metrics

router = APIRouter()
metrics_service = MetricsService()
engagement_service = EngagementDetectionService()


@router.get("/teams/{team_id}/summary", response_model=TeamSummary)
async def get_team_summary(
    team_id: int,
    week_start: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team-level summary"""
    if not check_permission(current_user, target_team_id=team_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this team"
        )
    
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )
    
    if not week_start:
        week_start = get_week_start(datetime.utcnow()).date()
    
    # Get all team members
    team_users = db.query(User).filter(
        User.team_id == team_id,
        User.is_active == True
    ).all()
    
    # Get metrics for each user
    members = []
    healthy_count = 0
    watch_count = 0
    needs_review_count = 0
    total_score = 0.0
    score_count = 0
    
    for user in team_users:
        try:
            user_summary = await get_user_metrics(
                user_id=user.id,
                weeks=8,
                current_user=current_user,
                db=db
            )
            members.append(user_summary)
            
            # Count by status
            status = user_summary.engagement_status
            if status == "healthy":
                healthy_count += 1
            elif status == "watch":
                watch_count += 1
            elif status == "needs_review":
                needs_review_count += 1
            
            # Calculate average score
            if user_summary.current_week.composite_score:
                total_score += user_summary.current_week.composite_score
                score_count += 1
        except Exception as e:
            # Skip users we can't access
            continue
    
    avg_score = total_score / score_count if score_count > 0 else 0.0
    
    return TeamSummary(
        team_id=team.id,
        team_name=team.name,
        total_members=len(team_users),
        healthy_count=healthy_count,
        watch_count=watch_count,
        needs_review_count=needs_review_count,
        average_composite_score=avg_score,
        members=members
    )


@router.get("/weekly", response_model=WeeklyReport)
async def get_weekly_report(
    week_start: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weekly report for all teams (admin/manager only)"""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and managers can access weekly reports"
        )
    
    if not week_start:
        week_start = get_week_start(datetime.utcnow()).date()
    
    # Get teams based on user role
    if current_user.role == "admin":
        teams = db.query(Team).all()
    else:
        # Manager can only see their team
        teams = db.query(Team).filter(Team.id == current_user.team_id).all()
    
    team_summaries = []
    total_users = 0
    total_healthy = 0
    total_watch = 0
    total_needs_review = 0
    
    for team in teams:
        try:
            team_summary = await get_team_summary(
                team_id=team.id,
                week_start=week_start,
                current_user=current_user,
                db=db
            )
            team_summaries.append(team_summary)
            
            total_users += team_summary.total_members
            total_healthy += team_summary.healthy_count
            total_watch += team_summary.watch_count
            total_needs_review += team_summary.needs_review_count
        except Exception as e:
            continue
    
    return WeeklyReport(
        week_start=week_start,
        generated_at=datetime.utcnow(),
        teams=team_summaries,
        total_users=total_users,
        healthy_users=total_healthy,
        watch_users=total_watch,
        needs_review_users=total_needs_review
    )


@router.post("/overrides")
async def create_override(
    override_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create an override for engagement status (manager/admin only)"""
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and managers can create overrides"
        )
    
    user_id = override_data.get("user_id")
    week_start = override_data.get("week_start")
    reason = override_data.get("reason")
    flags = override_data.get("flags", {})
    notes = override_data.get("notes")
    
    if not all([user_id, week_start, reason]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields: user_id, week_start, reason"
        )
    
    # Check permission
    if not check_permission(current_user, target_user_id=user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create override for this user"
        )
    
    # Parse week_start if string
    if isinstance(week_start, str):
        week_start = datetime.fromisoformat(week_start).date()
    
    # Get or create weekly metrics
    weekly_metrics = db.query(WeeklyUserMetrics).filter(
        WeeklyUserMetrics.user_id == user_id,
        WeeklyUserMetrics.week_start == week_start
    ).first()
    
    if not weekly_metrics:
        # Create if doesn't exist
        weekly_metrics = metrics_service.aggregate_week(db, user_id, week_start)
    
    # Update flags and status
    if not weekly_metrics.flags:
        weekly_metrics.flags = {}
    
    weekly_metrics.flags.update(flags)
    weekly_metrics.flags["override"] = True
    weekly_metrics.flags["override_reason"] = reason
    weekly_metrics.flags["override_notes"] = notes
    weekly_metrics.flags["override_by"] = current_user.id
    weekly_metrics.flags["override_at"] = datetime.utcnow().isoformat()
    
    # Set status to healthy if override
    weekly_metrics.engagement_status = "healthy"
    
    db.commit()
    db.refresh(weekly_metrics)
    
    return {
        "id": weekly_metrics.id,
        "user_id": user_id,
        "week_start": week_start,
        "reason": reason,
        "created_at": datetime.utcnow()
    }

