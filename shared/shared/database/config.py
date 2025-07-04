# glam-app/shared/database/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, Dict, Any
import os


class DatabaseConfig(BaseSettings):
    """
    Base database configuration for microservices.
    Automatically handles Docker port mapping.
    
    When running locally against Docker:
    - DB_PORT_EXTERNAL is used if DB_HOST is localhost
    - DB_PORT is used when running inside Docker
    """
    
    # Connection parameters
    DB_HOST: str = Field(..., description="Database host")
    DB_PORT: Optional[int] = Field(default=None, description="Database port")
    DB_PORT_EXTERNAL: Optional[int] = Field(default=None, description="External port for Docker")
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
    
    # Async driver
    DB_ASYNC_DRIVER: str = Field(default="asyncpg", description="Async database driver")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    def model_post_init(self, __context):
        """Post-initialization to set the correct port"""
        # If DB_PORT is not explicitly set, determine it intelligently
        if self.DB_PORT is None:
            if self.DB_HOST in ['localhost', '127.0.0.1', 'host.docker.internal']:
                # Connecting from host to Docker container
                self.DB_PORT = self.DB_PORT_EXTERNAL or 5432
            else:
                # Connecting within Docker network or to remote host
                self.DB_PORT = 5432
    
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
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_pre_ping": self.DB_POOL_PRE_PING,
            "pool_recycle": self.DB_POOL_RECYCLE,
        }


def create_database_config(prefix: str = "") -> DatabaseConfig:
    """
    Factory function to create DatabaseConfig with custom prefix.
    
    Args:
        prefix: Environment variable prefix (e.g., "NOTIFICATION_")
    
    Returns:
        DatabaseConfig instance with prefixed env vars
    """
    class PrefixedDatabaseConfig(DatabaseConfig):
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=True,
            env_prefix=prefix,
        )
    
    return PrefixedDatabaseConfig() # type: ignore


class TestDatabaseConfig(DatabaseConfig):
    """Test database configuration"""
    
    DB_ECHO: bool = True
    
    class Config:
        env_file = ".env.test"