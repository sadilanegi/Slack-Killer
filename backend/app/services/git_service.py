"""
Git service for fetching and processing GitHub/GitLab PR and commit data
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.activity_event import ActivityEvent
from app.models.user import User


class GitService:
    """Service for interacting with GitHub API"""
    
    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.org = settings.GITHUB_ORG
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        } if self.token else {}
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to GitHub API"""
        if not self.token:
            # In development, return mock data
            return None
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"GitHub API error: {e}")
            return None
    
    def fetch_user_prs(
        self,
        user_github_username: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Fetch PRs authored by a user
        
        Args:
            user_github_username: GitHub username
            start_date: Start date for filtering
            end_date: End date for filtering
        
        Returns:
            List of PR dictionaries
        """
        if not self.org:
            return []
        
        url = f"https://api.github.com/search/issues"
        query = f"author:{user_github_username} type:pr org:{self.org} is:merged"
        
        if start_date:
            query += f" merged:>={start_date.strftime('%Y-%m-%d')}"
        if end_date:
            query += f" merged:<={end_date.strftime('%Y-%m-%d')}"
        
        params = {"q": query, "per_page": 100}
        
        result = self._make_request(url, params)
        if not result:
            return []
        
        prs = []
        for item in result.get("items", []):
            pr = {
                "number": item.get("number"),
                "title": item.get("title"),
                "merged_at": item.get("pull_request", {}).get("merged_at"),
                "created_at": item.get("created_at"),
                "url": item.get("html_url"),
            }
            prs.append(pr)
        
        return prs
    
    def fetch_user_pr_reviews(
        self,
        user_github_username: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Fetch PRs reviewed by a user
        
        Args:
            user_github_username: GitHub username
            start_date: Start date for filtering
            end_date: End date for filtering
        
        Returns:
            List of review dictionaries
        """
        if not self.org:
            return []
        
        # GitHub search for PRs with reviews by user
        url = f"https://api.github.com/search/issues"
        query = f"reviewed-by:{user_github_username} type:pr org:{self.org}"
        
        if start_date:
            query += f" updated:>={start_date.strftime('%Y-%m-%d')}"
        if end_date:
            query += f" updated:<={end_date.strftime('%Y-%m-%d')}"
        
        params = {"q": query, "per_page": 100}
        
        result = self._make_request(url, params)
        if not result:
            return []
        
        reviews = []
        for item in result.get("items", []):
            review = {
                "pr_number": item.get("number"),
                "pr_title": item.get("title"),
                "updated_at": item.get("updated_at"),
                "url": item.get("html_url"),
            }
            reviews.append(review)
        
        return reviews
    
    def fetch_user_commits(
        self,
        user_github_username: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Fetch commits by a user
        
        Note: This requires repository-level access, so we'll use a simplified approach
        """
        if not self.org:
            return []
        
        # For production, you'd need to iterate through repos
        # This is a simplified version
        url = f"https://api.github.com/search/commits"
        query = f"author:{user_github_username} org:{self.org}"
        
        if start_date:
            query += f" author-date:>={start_date.strftime('%Y-%m-%d')}"
        if end_date:
            query += f" author-date:<={end_date.strftime('%Y-%m-%d')}"
        
        headers = self.headers.copy()
        headers["Accept"] = "application/vnd.github.cloak-preview+json"
        
        try:
            response = requests.get(url, headers=headers, params={"q": query}, timeout=30)
            response.raise_for_status()
            result = response.json()
        except requests.RequestException as e:
            print(f"GitHub commits API error: {e}")
            return []
        
        commits = []
        for item in result.get("items", []):
            commit = {
                "sha": item.get("sha"),
                "message": item.get("commit", {}).get("message"),
                "date": item.get("commit", {}).get("author", {}).get("date"),
                "url": item.get("html_url"),
            }
            commits.append(commit)
        
        return commits
    
    def sync_user_activity(
        self,
        db: Session,
        user: User,
        github_username: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Sync GitHub activity as activity events for a user
        
        Args:
            db: Database session
            user: User object
            github_username: GitHub username (if different from email)
            start_date: Start date for syncing
            end_date: End date for syncing
        
        Returns:
            Number of events created
        """
        if not github_username:
            # Try to extract from email or use email as fallback
            github_username = user.email.split("@")[0]
        
        events_created = 0
        
        # Sync PRs authored
        prs = self.fetch_user_prs(github_username, start_date, end_date)
        for pr in prs:
            existing = db.query(ActivityEvent).filter(
                ActivityEvent.user_id == user.id,
                ActivityEvent.source == "github",
                ActivityEvent.event_type == "pr_merged",
                ActivityEvent.event_metadata["number"].astext == str(pr["number"])
            ).first()
            
            if existing:
                continue
            
            merged_at = None
            if pr.get("merged_at"):
                try:
                    merged_at = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
                except:
                    merged_at = datetime.utcnow()
            else:
                merged_at = datetime.utcnow()
            
            event = ActivityEvent(
                user_id=user.id,
                source="github",
                event_type="pr_merged",
                occurred_at=merged_at,
                event_metadata={
                    "number": pr["number"],
                    "title": pr.get("title"),
                    "url": pr.get("url"),
                }
            )
            db.add(event)
            events_created += 1
        
        # Sync PR reviews
        reviews = self.fetch_user_pr_reviews(github_username, start_date, end_date)
        for review in reviews:
            existing = db.query(ActivityEvent).filter(
                ActivityEvent.user_id == user.id,
                ActivityEvent.source == "github",
                ActivityEvent.event_type == "pr_reviewed",
                ActivityEvent.event_metadata["pr_number"].astext == str(review["pr_number"])
            ).first()
            
            if existing:
                continue
            
            updated_at = None
            if review.get("updated_at"):
                try:
                    updated_at = datetime.fromisoformat(review["updated_at"].replace("Z", "+00:00"))
                except:
                    updated_at = datetime.utcnow()
            else:
                updated_at = datetime.utcnow()
            
            event = ActivityEvent(
                user_id=user.id,
                source="github",
                event_type="pr_reviewed",
                occurred_at=updated_at,
                event_metadata={
                    "pr_number": review["pr_number"],
                    "pr_title": review.get("pr_title"),
                    "url": review.get("url"),
                }
            )
            db.add(event)
            events_created += 1
        
        # Sync commits (batch by day to avoid too many events)
        commits = self.fetch_user_commits(github_username, start_date, end_date)
        # Group commits by day
        commits_by_day = {}
        for commit in commits:
            if commit.get("date"):
                try:
                    commit_date = datetime.fromisoformat(commit["date"].replace("Z", "+00:00"))
                    day_key = commit_date.date()
                    if day_key not in commits_by_day:
                        commits_by_day[day_key] = []
                    commits_by_day[day_key].append(commit)
                except:
                    pass
        
        for day, day_commits in commits_by_day.items():
            existing = db.query(ActivityEvent).filter(
                ActivityEvent.user_id == user.id,
                ActivityEvent.source == "github",
                ActivityEvent.event_type == "commits",
                ActivityEvent.occurred_at >= datetime.combine(day, datetime.min.time()),
                ActivityEvent.occurred_at < datetime.combine(day, datetime.min.time()).replace(day=day.day + 1) if day.day < 28 else datetime.combine(day.replace(day=1, month=day.month + 1), datetime.min.time())
            ).first()
            
            if existing:
                # Update count
                existing.event_metadata = existing.event_metadata or {}
                existing.event_metadata["count"] = len(day_commits)
                continue
            
            event = ActivityEvent(
                user_id=user.id,
                source="github",
                event_type="commits",
                occurred_at=datetime.combine(day, datetime.min.time()),
                event_metadata={
                    "count": len(day_commits),
                    "commits": [{"sha": c.get("sha"), "message": c.get("message")} for c in day_commits[:10]]  # Store first 10
                }
            )
            db.add(event)
            events_created += 1
        
        db.commit()
        return events_created
    
    def sync_all_users(self, db: Session, start_date: Optional[datetime] = None) -> Dict[str, int]:
        """
        Sync GitHub activity for all active users
        
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
                print(f"Error syncing GitHub for user {user.id}: {e}")
                stats["errors"] += 1
        
        return stats

