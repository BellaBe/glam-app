# services/scheduler-service/src/models/database.py
"""Database initialization for scheduler service"""

from shared.database.base import Base
from .schedule import Schedule
from .execution import ScheduleExecution

# Import all models to ensure they're registered with SQLAlchemy
__all__ = ['Base', 'Schedule', 'ScheduleExecution']