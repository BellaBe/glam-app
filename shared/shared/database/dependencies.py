# glam-app/shared/database/dependencies.py
from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .session import DatabaseSessionManager

# Global database manager instance - each service will set this
from typing import Optional

_db_manager: Optional[DatabaseSessionManager] = None


def set_database_manager(manager: DatabaseSessionManager):
    """Set the global database manager for the service"""
    global _db_manager
    _db_manager = manager


def get_database_manager() -> DatabaseSessionManager:
    """Get the current database manager"""
    if _db_manager is None:
        raise RuntimeError(
            "Database manager not initialized. "
            "Call set_database_manager() during app startup."
        )
    return _db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to get a database session"""
    manager = get_database_manager()
    async with manager.session() as session:
        yield session
        
async def get_database_health() -> bool:
    """Check if the database is healthy"""
    manager = get_database_manager()
    try:
        async with manager.session() as session:
            # Perform a simple query to check connectivity
            from sqlalchemy.sql import text
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        # Log the error or handle it as needed
        print(f"Database health check failed: {e}")
        return False


# Type alias for dependency injection
DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]