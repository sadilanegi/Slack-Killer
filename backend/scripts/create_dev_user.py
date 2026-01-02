"""
Script to create a development user for testing
Run this after setting up the database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, Team
from datetime import date

def create_dev_user():
    db = SessionLocal()
    try:
        # Create a default team if it doesn't exist
        team = db.query(Team).filter(Team.name == "Engineering").first()
        if not team:
            team = Team(name="Engineering", description="Engineering Team")
            db.add(team)
            db.commit()
            db.refresh(team)
        
        # Create admin user
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            admin = User(
                name="Admin User",
                email="admin@example.com",
                role="admin",
                team_id=team.id,
                is_active=True
            )
            db.add(admin)
            db.commit()
            print(f"Created admin user: {admin.email}")
        
        # Create manager user
        manager = db.query(User).filter(User.email == "manager@example.com").first()
        if not manager:
            manager = User(
                name="Manager User",
                email="manager@example.com",
                role="manager",
                team_id=team.id,
                is_active=True
            )
            db.add(manager)
            db.commit()
            print(f"Created manager user: {manager.email}")
        
        # Create engineer user
        engineer = db.query(User).filter(User.email == "engineer@example.com").first()
        if not engineer:
            engineer = User(
                name="Engineer User",
                email="engineer@example.com",
                role="backend",
                team_id=team.id,
                is_active=True
            )
            db.add(engineer)
            db.commit()
            print(f"Created engineer user: {engineer.email}")
        
        print("\nDevelopment users created successfully!")
        print("You can now use these emails to login:")
        print("  - admin@example.com (admin)")
        print("  - manager@example.com (manager)")
        print("  - engineer@example.com (engineer)")
        
    except Exception as e:
        print(f"Error creating dev user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_dev_user()

