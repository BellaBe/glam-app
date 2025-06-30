# glam-app/shared/database/__init__.py
"""
Shared database utilities for GLAM microservices.

This package provides:
- Base SQLAlchemy models and mixins
- Async session management
- Generic repository pattern
- FastAPI dependencies
- Alembic migration utilities
- Database configuration
"""

from .base import Base, TimestampedMixin, SoftDeleteMixin
from .session import DatabaseSessionManager
from .repository import Repository, SoftDeleteRepository
from .dependencies import (
    DBSessionDep,
    get_db_session,
    set_database_manager,
    get_database_manager
)
from .config import DatabaseConfig, TestDatabaseConfig
from .migrations import MigrationManager, create_alembic_env_template

__all__ = [
    # Base classes
    "Base",
    "TimestampedMixin",
    "SoftDeleteMixin",
    
    # Session management
    "DatabaseSessionManager",
    
    # Repository pattern
    "Repository",
    "SoftDeleteRepository",
    
    # FastAPI dependencies
    "DBSessionDep",
    "get_db_session",
    "set_database_manager",
    "get_database_manager",
    
    # Configuration
    "DatabaseConfig",
    "TestDatabaseConfig",
    
    # Migrations
    "MigrationManager",
    "create_alembic_env_template",
]