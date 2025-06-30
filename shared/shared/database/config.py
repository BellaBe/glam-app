# glam-app/shared/database/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, Dict, Any


class DatabaseConfig(BaseSettings):
    """
    Base database configuration for microservices.
    Environment variables are set by Docker Compose from the root .env file.
    
    Docker Compose will set these per service:
    - DB_HOST: Database host (e.g., user-db, order-db)
    - DB_PORT: Database port (always 5432 inside Docker network)
    - DB_NAME: Database name
    - DB_USER: Database user
    - DB_PASSWORD: Database password
    """
    
    # Connection parameters - set by Docker Compose
    DB_HOST: str = Field(..., description="Database host")
    DB_PORT: int = Field(default=5432, description="Database port")
    DB_NAME: str = Field(..., description="Database name")
    DB_USER: str = Field(..., description="Database user")
    DB_PASSWORD: str = Field(..., description="Database password")
    
    # Optional schema for logical separation
    DB_SCHEMA: Optional[str] = Field(default=None, description="Database schema")
    
    # Connection pool settings
    DB_POOL_SIZE: int = Field(default=5, description="Connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=10, description="Max overflow connections")
    DB_POOL_PRE_PING: bool = Field(default=True, description="Pre-ping connections")
    DB_POOL_RECYCLE: int = Field(default=3600, description="Recycle connections after seconds")
    
    # SQLAlchemy settings
    DB_ECHO: bool = Field(default=False, description="Echo SQL statements")
    DB_ECHO_POOL: bool = Field(default=False, description="Echo pool events")
    
    # Async driver
    DB_ASYNC_DRIVER: str = Field(default="asyncpg", description="Async database driver")
    
    
    model_config = SettingsConfigDict(
        env_file=".env",  # Default environment file
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    @property
    def database_url(self) -> str:
        """Construct the async database URL"""
        return (
            f"postgresql+{self.DB_ASYNC_DRIVER}://"
            f"{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    @property
    def sync_database_url(self) -> str:
        """Construct sync database URL (for Alembic)"""
        return (
            f"postgresql://"
            f"{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    @property
    def display_url(self) -> str:
        """Get a display-safe URL (password hidden)"""
        return (
            f"postgresql+{self.DB_ASYNC_DRIVER}://"
            f"{self.DB_USER}:***@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    def get_engine_kwargs(self) -> Dict[str, Any]:
        """Get kwargs for create_async_engine"""
        return {
            "echo": self.DB_ECHO,
            "echo_pool": self.DB_ECHO_POOL,
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_pre_ping": self.DB_POOL_PRE_PING,
            "pool_recycle": self.DB_POOL_RECYCLE,
        }
        


class TestDatabaseConfig(DatabaseConfig):
    """Test database configuration"""
    
    DB_ECHO: bool = True
    
    
    class Config: # type: ignore
        env_file = ".env.test" 