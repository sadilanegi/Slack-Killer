"""
Engagement detection service for identifying low engagement patterns
⚠️ Uses neutral language: engagement_risk, watch, needs_review (NOT "slacker")
"""
from typing import Optional, List
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from app.models.weekly_metrics import WeeklyUserMetrics
from app.models.user import User
from app.core.config import settings
from app.utils.time import get_week_start, get_weeks_ago


class EngagementDetectionService:
    """Service for detecting low engagement patterns"""
    
    def check_exceptions(
        self,
        flags: Optional[dict],
        week_start: date
    ) -> bool:
        """
        Check if user has valid exceptions for low activity
        
        Returns:
            True if exception applies, False otherwise
        """
        if not flags:
            return False
        
        # Check for PTO
        if flags.get("pto"):
            pto_start = flags.get("pto_start")
            pto_end = flags.get("pto_end")
            if pto_start and pto_end:
                try:
                    pto_start_date = datetime.fromisoformat(str(pto_start)).date() if isinstance(pto_start, str) else pto_start
                    pto_end_date = datetime.fromisoformat(str(pto_end)).date() if isinstance(pto_end, str) else pto_end
                    if pto_start_date <= week_start <= pto_end_date:
                        return True
                except:
                    pass
        
        # Check for onboarding
        if flags.get("onboarding") and flags.get("onboarding_until"):
            onboarding_until = flags.get("onboarding_until")
            try:
                onboarding_until_date = datetime.fromisoformat(str(onboarding_until)).date() if isinstance(onboarding_until, str) else onboarding_until
                if week_start <= onboarding_until_date:
                    return True
            except:
                pass
        
        # Check for role change
        if flags.get("role_change") and flags.get("role_change_date"):
            role_change_date = flags.get("role_change_date")
            try:
                role_change_date_obj = datetime.fromisoformat(str(role_change_date)).date() if isinstance(role_change_date, str) else role_change_date
                # Allow 2 weeks grace period after role change
                from datetime import timedelta
                if week_start <= role_change_date_obj + timedelta(weeks=2):
                    return True
            except:
                pass
        
        # Check for on-call duty (may reduce other activity)
        if flags.get("on_call") and flags.get("on_call_week"):
            if flags.get("on_call_week") == str(week_start):
                return True
        
        return False
    
    def detect_engagement_status(
        self,
        db: Session,
        user_id: int,
        week_start: date,
        weekly_metrics: WeeklyUserMetrics
    ) -> str:
        """
        Detect engagement status for a user in a given week
        
        Returns:
            "healthy", "watch", or "needs_review"
        """
        # Check for exceptions first
        if self.check_exceptions(weekly_metrics.flags, week_start):
            return "healthy"
        
        baseline = weekly_metrics.baseline_score
        composite = weekly_metrics.composite_score
        
        if baseline is None or composite is None:
            # Not enough data yet
            return "healthy"
        
        # Rule 1: Below threshold for N weeks
        recent_weeks = self.get_recent_weeks_metrics(db, user_id, week_start, settings.NEEDS_REVIEW_WEEKS)
        
        if len(recent_weeks) >= settings.NEEDS_REVIEW_WEEKS:
            below_threshold_count = sum(
                1 for wm in recent_weeks
                if wm.composite_score is not None
                and wm.baseline_score is not None
                and wm.composite_score < (wm.baseline_score * (1 - settings.LOW_ENGAGEMENT_THRESHOLD))
                and not self.check_exceptions(wm.flags, wm.week_start)
            )
            
            if below_threshold_count >= settings.NEEDS_REVIEW_WEEKS:
                return "needs_review"
        
        if len(recent_weeks) >= settings.WATCH_WEEKS:
            below_threshold_count = sum(
                1 for wm in recent_weeks
                if wm.composite_score is not None
                and wm.baseline_score is not None
                and wm.composite_score < (wm.baseline_score * (1 - settings.LOW_ENGAGEMENT_THRESHOLD))
                and not self.check_exceptions(wm.flags, wm.week_start)
            )
            
            if below_threshold_count >= settings.WATCH_WEEKS:
                return "watch"
        
        # Rule 2: Sudden drop (>40% vs baseline)
        if composite < (baseline * (1 - settings.SUDDEN_DROP_THRESHOLD)):
            # Check previous week to confirm it's a sudden drop
            previous_week = self.get_previous_week_metrics(db, user_id, week_start)
            if previous_week and previous_week.composite_score:
                if previous_week.composite_score >= (baseline * 0.9):  # Was healthy before
                    return "watch"
        
        # Rule 3: Low collaboration (PR reviews/comments)
        if weekly_metrics.prs_reviewed == 0 and weekly_metrics.prs_authored > 0:
            # Authored PRs but no reviews - low collaboration
            # Only flag if this is a pattern
            recent_reviews = sum(wm.prs_reviewed for wm in recent_weeks[:4])
            if recent_reviews == 0 and len(recent_weeks) >= 2:
                return "watch"
        
        # Rule 4: Sustained inactivity (all metrics near zero)
        if (weekly_metrics.tickets_completed == 0 and
            weekly_metrics.prs_authored == 0 and
            weekly_metrics.commits == 0 and
            weekly_metrics.docs_authored == 0):
            # Check if this is sustained
            inactive_weeks = sum(
                1 for wm in recent_weeks[:2]
                if wm.tickets_completed == 0
                and wm.prs_authored == 0
                and wm.commits == 0
                and not self.check_exceptions(wm.flags, wm.week_start)
            )
            if inactive_weeks >= 2:
                return "watch"
        
        return "healthy"
    
    def get_recent_weeks_metrics(
        self,
        db: Session,
        user_id: int,
        week_start: date,
        weeks: int
    ) -> List[WeeklyUserMetrics]:
        """Get metrics for recent N weeks"""
        cutoff_date = get_weeks_ago(weeks)
        
        metrics = db.query(WeeklyUserMetrics).filter(
            WeeklyUserMetrics.user_id == user_id,
            WeeklyUserMetrics.week_start >= cutoff_date.date(),
            WeeklyUserMetrics.week_start <= week_start
        ).order_by(desc(WeeklyUserMetrics.week_start)).limit(weeks).all()
        
        return metrics
    
    def get_previous_week_metrics(
        self,
        db: Session,
        user_id: int,
        week_start: date
    ) -> Optional[WeeklyUserMetrics]:
        """Get metrics for the previous week"""
        from datetime import timedelta
        previous_week_start = week_start - timedelta(days=7)
        
        return db.query(WeeklyUserMetrics).filter(
            WeeklyUserMetrics.user_id == user_id,
            WeeklyUserMetrics.week_start == previous_week_start
        ).first()
    
    def update_engagement_status(
        self,
        db: Session,
        user_id: int,
        week_start: date
    ) -> WeeklyUserMetrics:
        """
        Update engagement status for a user's weekly metrics
        
        Returns:
            Updated WeeklyUserMetrics object
        """
        weekly_metrics = db.query(WeeklyUserMetrics).filter(
            WeeklyUserMetrics.user_id == user_id,
            WeeklyUserMetrics.week_start == week_start
        ).first()
        
        if not weekly_metrics:
            raise ValueError(f"Weekly metrics not found for user {user_id}, week {week_start}")
        
        engagement_status = self.detect_engagement_status(db, user_id, week_start, weekly_metrics)
        weekly_metrics.engagement_status = engagement_status
        
        db.commit()
        db.refresh(weekly_metrics)
        
        return weekly_metrics

