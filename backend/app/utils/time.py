"""
Time utility functions for date calculations
"""
from datetime import datetime, timedelta
from typing import Tuple


def get_week_start(date: datetime) -> datetime:
    """
    Get the start of the week (Monday) for a given date
    """
    days_since_monday = date.weekday()
    week_start = date - timedelta(days=days_since_monday)
    return week_start.replace(hour=0, minute=0, second=0, microsecond=0)


def get_week_range(date: datetime) -> Tuple[datetime, datetime]:
    """
    Get the start and end of the week for a given date
    Returns: (week_start, week_end)
    """
    week_start = get_week_start(date)
    week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return (week_start, week_end)


def get_weeks_ago(weeks: int) -> datetime:
    """
    Get datetime for N weeks ago
    """
    return datetime.utcnow() - timedelta(weeks=weeks)


def is_same_week(date1: datetime, date2: datetime) -> bool:
    """
    Check if two dates are in the same week
    """
    return get_week_start(date1) == get_week_start(date2)

