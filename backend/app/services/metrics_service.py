"""
Metrics service for calculating and normalizing productivity metrics
"""
from typing import Dict, List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.activity_event import ActivityEvent
from app.models.weekly_metrics import WeeklyUserMetrics
from app.models.user import User
from app.core.config import settings
from app.utils.time import get_week_start


class MetricsService:
    """Service for calculating and aggregating metrics"""
    
    def calculate_weekly_metrics(
        self,
        db: Session,
        user_id: int,
        week_start: date
    ) -> Dict:
        """
        Calculate weekly metrics for a user from activity events
        
        Returns:
            Dictionary with all calculated metrics
        """
        week_end = datetime.combine(week_start, datetime.max.time())
        week_start_dt = datetime.combine(week_start, datetime.min.time())
        
        # Query all activity events for the week
        events = db.query(ActivityEvent).filter(
            ActivityEvent.user_id == user_id,
            ActivityEvent.occurred_at >= week_start_dt,
            ActivityEvent.occurred_at <= week_end
        ).all()
        
        metrics = {
            "tickets_completed": 0,
            "story_points": 0.0,
            "prs_authored": 0,
            "prs_reviewed": 0,
            "commits": 0,
            "docs_authored": 0,
            "meeting_hours": 0.0,
        }
        
        for event in events:
            if event.source == "jira" and event.event_type == "ticket_completed":
                metrics["tickets_completed"] += 1
                if event.event_metadata and "story_points" in event.event_metadata:
                    metrics["story_points"] += float(event.event_metadata.get("story_points", 0))
            
            elif event.source == "github":
                if event.event_type == "pr_merged":
                    metrics["prs_authored"] += 1
                elif event.event_type == "pr_reviewed":
                    metrics["prs_reviewed"] += 1
                elif event.event_type == "commits":
                    if event.event_metadata and "count" in event.event_metadata:
                        metrics["commits"] += int(event.event_metadata.get("count", 0))
            
            elif event.source == "docs" and event.event_type == "doc_created":
                metrics["docs_authored"] += 1
            
            elif event.source == "calendar" and event.event_type == "meeting":
                if event.event_metadata and "duration_hours" in event.event_metadata:
                    metrics["meeting_hours"] += float(event.event_metadata.get("duration_hours", 0))
        
        return metrics
    
    def get_role_averages(
        self,
        db: Session,
        role: str,
        week_start: date,
        exclude_user_id: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calculate average metrics for a role in a given week
        
        Returns:
            Dictionary with average values and standard deviations
        """
        query = db.query(WeeklyUserMetrics).join(User).filter(
            User.role == role,
            WeeklyUserMetrics.week_start == week_start,
            User.is_active == True
        )
        
        if exclude_user_id:
            query = query.filter(WeeklyUserMetrics.user_id != exclude_user_id)
        
        metrics_list = query.all()
        
        if not metrics_list:
            return {
                "avg_tickets": 0.0,
                "avg_story_points": 0.0,
                "avg_prs_authored": 0.0,
                "avg_prs_reviewed": 0.0,
                "avg_commits": 0.0,
                "avg_docs": 0.0,
                "avg_meetings": 0.0,
                "std_tickets": 1.0,
                "std_story_points": 1.0,
                "std_prs_authored": 1.0,
                "std_prs_reviewed": 1.0,
                "std_commits": 1.0,
                "std_docs": 1.0,
                "std_meetings": 1.0,
            }
        
        # Calculate averages
        n = len(metrics_list)
        avg_tickets = sum(m.tickets_completed for m in metrics_list) / n
        avg_story_points = sum(m.story_points for m in metrics_list) / n
        avg_prs_authored = sum(m.prs_authored for m in metrics_list) / n
        avg_prs_reviewed = sum(m.prs_reviewed for m in metrics_list) / n
        avg_commits = sum(m.commits for m in metrics_list) / n
        avg_docs = sum(m.docs_authored for m in metrics_list) / n
        avg_meetings = sum(m.meeting_hours for m in metrics_list) / n
        
        # Calculate standard deviations
        import statistics
        std_tickets = statistics.stdev([m.tickets_completed for m in metrics_list]) if n > 1 else 1.0
        std_story_points = statistics.stdev([m.story_points for m in metrics_list]) if n > 1 else 1.0
        std_prs_authored = statistics.stdev([m.prs_authored for m in metrics_list]) if n > 1 else 1.0
        std_prs_reviewed = statistics.stdev([m.prs_reviewed for m in metrics_list]) if n > 1 else 1.0
        std_commits = statistics.stdev([m.commits for m in metrics_list]) if n > 1 else 1.0
        std_docs = statistics.stdev([m.docs_authored for m in metrics_list]) if n > 1 else 1.0
        std_meetings = statistics.stdev([m.meeting_hours for m in metrics_list]) if n > 1 else 1.0
        
        return {
            "avg_tickets": avg_tickets,
            "avg_story_points": avg_story_points,
            "avg_prs_authored": avg_prs_authored,
            "avg_prs_reviewed": avg_prs_reviewed,
            "avg_commits": avg_commits,
            "avg_docs": avg_docs,
            "avg_meetings": avg_meetings,
            "std_tickets": max(std_tickets, 0.1),  # Avoid division by zero
            "std_story_points": max(std_story_points, 0.1),
            "std_prs_authored": max(std_prs_authored, 0.1),
            "std_prs_reviewed": max(std_prs_reviewed, 0.1),
            "std_commits": max(std_commits, 0.1),
            "std_docs": max(std_docs, 0.1),
            "std_meetings": max(std_meetings, 0.1),
        }
    
    def normalize_metrics(
        self,
        metrics: Dict,
        role: str,
        role_averages: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Normalize metrics using role-based averages
        
        Formula: normalized = (value - avg) / stddev
        """
        normalized = {}
        
        normalized["tickets"] = (
            (metrics["tickets_completed"] - role_averages["avg_tickets"]) / role_averages["std_tickets"]
            if role_averages["std_tickets"] > 0 else 0.0
        )
        normalized["story_points"] = (
            (metrics["story_points"] - role_averages["avg_story_points"]) / role_averages["std_story_points"]
            if role_averages["std_story_points"] > 0 else 0.0
        )
        normalized["prs_authored"] = (
            (metrics["prs_authored"] - role_averages["avg_prs_authored"]) / role_averages["std_prs_authored"]
            if role_averages["std_prs_authored"] > 0 else 0.0
        )
        normalized["prs_reviewed"] = (
            (metrics["prs_reviewed"] - role_averages["avg_prs_reviewed"]) / role_averages["std_prs_reviewed"]
            if role_averages["std_prs_reviewed"] > 0 else 0.0
        )
        normalized["commits"] = (
            (metrics["commits"] - role_averages["avg_commits"]) / role_averages["std_commits"]
            if role_averages["std_commits"] > 0 else 0.0
        )
        normalized["docs"] = (
            (metrics["docs_authored"] - role_averages["avg_docs"]) / role_averages["std_docs"]
            if role_averages["std_docs"] > 0 else 0.0
        )
        normalized["meetings"] = (
            (metrics["meeting_hours"] - role_averages["avg_meetings"]) / role_averages["std_meetings"]
            if role_averages["std_meetings"] > 0 else 0.0
        )
        
        return normalized
    
    def calculate_composite_score(
        self,
        normalized_metrics: Dict[str, float],
        role: str
    ) -> float:
        """
        Calculate composite score (0-100) using role-specific weights
        
        Args:
            normalized_metrics: Normalized metric values
            role: User role
        
        Returns:
            Composite score between 0-100
        """
        weights = settings.COMPOSITE_SCORE_WEIGHTS.get(role, settings.COMPOSITE_SCORE_WEIGHTS["backend"])
        
        # Convert normalized scores to 0-100 scale
        # Using sigmoid-like function: 50 + (normalized * 10), clamped to 0-100
        score = 0.0
        
        score += (50 + (normalized_metrics["tickets"] * 10)) * weights["tickets"]
        score += (50 + (normalized_metrics["story_points"] * 10)) * weights["story_points"]
        score += (50 + (normalized_metrics["prs_authored"] * 10)) * weights["prs_authored"]
        score += (50 + (normalized_metrics["prs_reviewed"] * 10)) * weights["prs_reviewed"]
        score += (50 + (normalized_metrics["commits"] * 10)) * weights["commits"]
        score += (50 + (normalized_metrics["docs"] * 10)) * weights["docs"]
        score += (50 + (normalized_metrics["meetings"] * 10)) * weights["meetings"]
        
        # Clamp to 0-100
        score = max(0.0, min(100.0, score))
        
        return score
    
    def calculate_baseline_score(
        self,
        db: Session,
        user_id: int,
        weeks: int = 8
    ) -> Optional[float]:
        """
        Calculate baseline score from historical data
        
        Args:
            db: Database session
            user_id: User ID
            weeks: Number of weeks to look back
        
        Returns:
            Average composite score over the period
        """
        from app.utils.time import get_weeks_ago
        
        cutoff_date = get_weeks_ago(weeks)
        
        metrics = db.query(WeeklyUserMetrics).filter(
            WeeklyUserMetrics.user_id == user_id,
            WeeklyUserMetrics.week_start >= cutoff_date.date(),
            WeeklyUserMetrics.composite_score.isnot(None)
        ).all()
        
        if not metrics:
            return None
        
        scores = [m.composite_score for m in metrics if m.composite_score is not None]
        if not scores:
            return None
        
        return sum(scores) / len(scores)
    
    def aggregate_week(
        self,
        db: Session,
        user_id: int,
        week_start: date
    ) -> WeeklyUserMetrics:
        """
        Aggregate activity events into weekly metrics for a user
        
        Returns:
            WeeklyUserMetrics object
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Calculate raw metrics
        raw_metrics = self.calculate_weekly_metrics(db, user_id, week_start)
        
        # Get role averages for normalization
        role_averages = self.get_role_averages(db, user.role, week_start, exclude_user_id=user_id)
        
        # Normalize metrics
        normalized = self.normalize_metrics(raw_metrics, user.role, role_averages)
        
        # Calculate composite score
        composite_score = self.calculate_composite_score(normalized, user.role)
        
        # Get baseline score
        baseline_score = self.calculate_baseline_score(db, user_id)
        
        # Get or create weekly metrics
        weekly_metrics = db.query(WeeklyUserMetrics).filter(
            WeeklyUserMetrics.user_id == user_id,
            WeeklyUserMetrics.week_start == week_start
        ).first()
        
        if not weekly_metrics:
            weekly_metrics = WeeklyUserMetrics(
                user_id=user_id,
                week_start=week_start
            )
            db.add(weekly_metrics)
        
        # Update metrics
        weekly_metrics.tickets_completed = raw_metrics["tickets_completed"]
        weekly_metrics.story_points = raw_metrics["story_points"]
        weekly_metrics.prs_authored = raw_metrics["prs_authored"]
        weekly_metrics.prs_reviewed = raw_metrics["prs_reviewed"]
        weekly_metrics.commits = raw_metrics["commits"]
        weekly_metrics.docs_authored = raw_metrics["docs_authored"]
        weekly_metrics.meeting_hours = raw_metrics["meeting_hours"]
        weekly_metrics.composite_score = composite_score
        weekly_metrics.baseline_score = baseline_score
        
        db.commit()
        db.refresh(weekly_metrics)
        
        return weekly_metrics

