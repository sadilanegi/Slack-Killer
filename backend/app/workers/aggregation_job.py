"""
Background job for aggregating activity events into weekly metrics
"""
import schedule
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.weekly_metrics import WeeklyUserMetrics
from app.services.metrics_service import MetricsService
from app.services.slack_detection import EngagementDetectionService
from app.services.jira_service import JiraService
from app.services.git_service import GitService
from app.utils.time import get_week_start, get_weeks_ago
from app.core.config import settings


class AggregationJob:
    """Background job for weekly metrics aggregation"""
    
    def __init__(self):
        self.metrics_service = MetricsService()
        self.engagement_service = EngagementDetectionService()
        self.jira_service = JiraService()
        self.git_service = GitService()
    
    def aggregate_current_week(self, db: Session):
        """Aggregate metrics for the current week for all active users"""
        current_week_start = get_week_start(datetime.utcnow()).date()
        users = db.query(User).filter(User.is_active == True).all()
        
        stats = {
            "users_processed": 0,
            "metrics_created": 0,
            "errors": 0
        }
        
        for user in users:
            try:
                # Aggregate week
                weekly_metrics = self.metrics_service.aggregate_week(
                    db, user.id, current_week_start
                )
                
                # Update engagement status
                self.engagement_service.update_engagement_status(
                    db, user.id, current_week_start
                )
                
                stats["metrics_created"] += 1
                stats["users_processed"] += 1
            except Exception as e:
                print(f"Error aggregating metrics for user {user.id}: {e}")
                stats["errors"] += 1
        
        return stats
    
    def sync_external_data(self, db: Session):
        """Sync data from external sources (Jira, GitHub)"""
        # Sync last 2 weeks of data
        start_date = get_weeks_ago(2)
        
        jira_stats = self.jira_service.sync_all_users(db, start_date=start_date)
        git_stats = self.git_service.sync_all_users(db, start_date=start_date)
        
        return {
            "jira": jira_stats,
            "github": git_stats
        }
    
    def run_full_aggregation(self):
        """Run full aggregation cycle"""
        db = SessionLocal()
        try:
            print(f"[{datetime.utcnow()}] Starting aggregation job...")
            
            # Step 1: Sync external data
            print("Syncing external data...")
            sync_stats = self.sync_external_data(db)
            print(f"Sync stats: {sync_stats}")
            
            # Step 2: Aggregate current week
            print("Aggregating current week metrics...")
            agg_stats = self.aggregate_current_week(db)
            print(f"Aggregation stats: {agg_stats}")
            
            # Step 3: Backfill missing weeks (last 4 weeks)
            print("Backfilling missing weeks...")
            for weeks_ago in range(1, 5):
                week_start = get_week_start(get_weeks_ago(weeks_ago)).date()
                users = db.query(User).filter(User.is_active == True).all()
                
                for user in users:
                    try:
                        existing = db.query(WeeklyUserMetrics).filter(
                            WeeklyUserMetrics.user_id == user.id,
                            WeeklyUserMetrics.week_start == week_start
                        ).first()
                        
                        if not existing:
                            self.metrics_service.aggregate_week(db, user.id, week_start)
                            self.engagement_service.update_engagement_status(
                                db, user.id, week_start
                            )
                    except Exception as e:
                        print(f"Error backfilling week {week_start} for user {user.id}: {e}")
            
            print(f"[{datetime.utcnow()}] Aggregation job completed")
            
        except Exception as e:
            print(f"Error in aggregation job: {e}")
            db.rollback()
        finally:
            db.close()
    
    def start_scheduler(self):
        """Start the scheduler for periodic aggregation"""
        # Schedule daily aggregation
        schedule.every(settings.AGGREGATION_JOB_INTERVAL_HOURS).hours.do(
            self.run_full_aggregation
        )
        
        print(f"Scheduler started. Running every {settings.AGGREGATION_JOB_INTERVAL_HOURS} hours.")
        
        # Run immediately on start
        self.run_full_aggregation()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


if __name__ == "__main__":
    job = AggregationJob()
    job.start_scheduler()

