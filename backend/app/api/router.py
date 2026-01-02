"""
Main API router that includes all route modules
"""
from fastapi import APIRouter
from app.api.routes import users, metrics, reports, auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

