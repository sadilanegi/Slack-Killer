"""
Application configuration using Pydantic settings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    # Default uses system user (no password for local development)
    # For production, set DATABASE_URL in .env file
    DATABASE_URL: str = "postgresql://mac@localhost:5432/productivity_db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # External API Keys
    JIRA_URL: str = ""
    JIRA_EMAIL: str = ""
    JIRA_API_TOKEN: str = ""
    
    GITHUB_TOKEN: str = ""
    GITHUB_ORG: str = ""
    
    # Metrics Configuration
    COMPOSITE_SCORE_WEIGHTS: dict = {
        "backend": {
            "tickets": 0.25,
            "story_points": 0.20,
            "prs_authored": 0.15,
            "prs_reviewed": 0.15,
            "commits": 0.10,
            "docs": 0.10,
            "meetings": 0.05
        },
        "frontend": {
            "tickets": 0.25,
            "story_points": 0.20,
            "prs_authored": 0.15,
            "prs_reviewed": 0.15,
            "commits": 0.10,
            "docs": 0.10,
            "meetings": 0.05
        },
        "devops": {
            "tickets": 0.20,
            "story_points": 0.15,
            "prs_authored": 0.15,
            "prs_reviewed": 0.15,
            "commits": 0.15,
            "docs": 0.15,
            "meetings": 0.05
        },
        "manager": {
            "tickets": 0.15,
            "story_points": 0.10,
            "prs_authored": 0.10,
            "prs_reviewed": 0.10,
            "commits": 0.05,
            "docs": 0.20,
            "meetings": 0.30
        }
    }
    
    # Engagement Detection Thresholds
    LOW_ENGAGEMENT_THRESHOLD: float = 0.3  # 30% below baseline
    SUDDEN_DROP_THRESHOLD: float = 0.4  # 40% drop
    WATCH_WEEKS: int = 2  # Weeks below threshold to trigger watch
    NEEDS_REVIEW_WEEKS: int = 3  # Weeks below threshold to trigger needs_review
    
    # Background Jobs
    AGGREGATION_JOB_INTERVAL_HOURS: int = 24
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

