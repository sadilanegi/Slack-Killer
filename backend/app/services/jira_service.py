"""
Jira service for fetching and processing ticket data
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.activity_event import ActivityEvent
from app.models.user import User


class JiraService:
    """Service for interacting with Jira API"""
    
    def __init__(self):
        self.base_url = settings.JIRA_URL
        self.email = settings.JIRA_EMAIL
        self.api_token = settings.JIRA_API_TOKEN
        self.auth = (self.email, self.api_token) if self.email and self.api_token else None
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to Jira API"""
        if not self.auth:
            # In development, return mock data
            return None
        
        url = f"{self.base_url}/rest/api/3/{endpoint}"
        try:
            response = requests.get(url, auth=self.auth, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Jira API error: {e}")
            return None
    
    def fetch_user_tickets(
        self,
        user_email: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Fetch completed tickets for a user
        
        Args:
            user_email: User's email address
            start_date: Start date for filtering
            end_date: End date for filtering
        
        Returns:
            List of ticket dictionaries
        """
        jql = f'assignee = "{user_email}" AND status = Done'
        
        if start_date:
            jql += f' AND resolved >= "{start_date.strftime("%Y-%m-%d")}"'
        if end_date:
            jql += f' AND resolved <= "{end_date.strftime("%Y-%m-%d")}"'
        
        params = {
            "jql": jql,
            "fields": "summary,status,resolutiondate,storyPoints,created,updated",
            "maxResults": 100
        }
        
        result = self._make_request("search", params)
        if not result:
            return []
        
        tickets = []
        for issue in result.get("issues", []):
            fields = issue.get("fields", {})
            ticket = {
                "key": issue.get("key"),
                "summary": fields.get("summary"),
                "resolution_date": fields.get("resolutiondate"),
                "story_points": fields.get("storyPoints") or 0,
                "created": fields.get("created"),
                "updated": fields.get("updated"),
            }
            tickets.append(ticket)
        
        return tickets
    
    def sync_user_activity(
        self,
        db: Session,
        user: User,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Sync Jira tickets as activity events for a user
        
        Args:
            db: Database session
            user: User object
            start_date: Start date for syncing
            end_date: End date for syncing
        
        Returns:
            Number of events created
        """
        tickets = self.fetch_user_tickets(user.email, start_date, end_date)
        
        events_created = 0
        for ticket in tickets:
            # Check if event already exists
            existing = db.query(ActivityEvent).filter(
                ActivityEvent.user_id == user.id,
                ActivityEvent.source == "jira",
                ActivityEvent.event_type == "ticket_completed",
                ActivityEvent.event_metadata["key"].astext == ticket["key"]
            ).first()
            
            if existing:
                continue
            
            # Parse resolution date
            resolution_date = None
            if ticket.get("resolution_date"):
                try:
                    resolution_date = datetime.fromisoformat(
                        ticket["resolution_date"].replace("Z", "+00:00")
                    )
                except:
                    resolution_date = datetime.utcnow()
            else:
                resolution_date = datetime.utcnow()
            
            # Create activity event
            event = ActivityEvent(
                user_id=user.id,
                source="jira",
                event_type="ticket_completed",
                occurred_at=resolution_date,
                event_metadata={
                    "key": ticket["key"],
                    "summary": ticket.get("summary"),
                    "story_points": ticket.get("story_points", 0),
                    "created": ticket.get("created"),
                    "updated": ticket.get("updated"),
                }
            )
            
            db.add(event)
            events_created += 1
        
        db.commit()
        return events_created
    
    def sync_all_users(self, db: Session, start_date: Optional[datetime] = None) -> Dict[str, int]:
        """
        Sync Jira activity for all active users
        
        Returns:
            Dictionary with sync statistics
        """
        users = db.query(User).filter(User.is_active == True).all()
        
        stats = {
            "users_processed": 0,
            "events_created": 0,
            "errors": 0
        }
        
        for user in users:
            try:
                events = self.sync_user_activity(db, user, start_date=start_date)
                stats["events_created"] += events
                stats["users_processed"] += 1
            except Exception as e:
                print(f"Error syncing Jira for user {user.id}: {e}")
                stats["errors"] += 1
        
        return stats

