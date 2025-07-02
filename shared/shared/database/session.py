# glam-app/shared/database/session.py
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseSessionManager:
    """
    Manages database connections and sessions for a microservice.
    Each service creates its own instance with its specific configuration.
    """
    
    def __init__(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_pre_ping: bool = True,
        pool_recycle: int = 3600
    ):
        self.database_url = database_url
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        
        # Engine configuration
        self.engine_config = {
            "echo": echo,
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_pre_ping": pool_pre_ping,
            "pool_recycle": pool_recycle,
        }
    
    async def init(self):
        """Initialize the database engine and session factory"""
        if self._engine is not None:
            raise RuntimeError("Database session manager already initialized")
        
        self._engine = create_async_engine(
            self.database_url,
            **self.engine_config
        )
        
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        logger.info(f"Database engine initialized with URL: {self.database_url}")
    
    async def close(self):
        """Close the database engine"""
        if self._engine is None:
            raise RuntimeError("Database session manager not initialized")
        
        await self._engine.dispose()
        self._engine = None
        self._session_factory = None
        logger.info("Database engine closed")
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Provide a transactional scope around a series of operations.
        Automatically commits on success and rolls back on error.
        """
        if self._session_factory is None:
            raise RuntimeError("Database session manager not initialized")
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Dependency injection function for FastAPI.
        Yields a database session and handles cleanup.
        """
        async with self.session() as session:
            yield session
    
    @property
    def engine(self) -> AsyncEngine:
        """Get the underlying SQLAlchemy engine"""
        if self._engine is None:
            raise RuntimeError("Database session manager not initialized")
        return self._engine
    
    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get the session factory"""
        if self._session_factory is None:
            raise RuntimeError("Database session manager not initialized")
        return self._session_factory