# File: services/connector-service/src/config.py

"""
Configuration for Connector Service.

Environment variables use CONNECTOR_ prefix to avoid conflicts.
"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from shared.database import DatabaseConfig

class ServiceConfig(BaseSettings):
    """Connector service configuration."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # Service Info
    SERVICE_NAME: str = "connector-service"
    SERVICE_VERSION: str = "0.1.0"
    ENV: str = Field("development", pattern="^(development|staging|production)$")
    LOG_LEVEL: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    
    # Database Configuration - uses CONNECTOR_ prefix
    DB_ENABLED: bool = True
    database_config: Optional[DatabaseConfig] = None
    
    # NATS Configuration
    NATS_SERVERS: str = "nats://localhost:4222"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/2"
    
    # Shopify Configuration
    SHOPIFY_API_VERSION: str = "2024-01"
    SHOPIFY_RATE_LIMIT: int = 4  # requests per second
    SHOPIFY_TIMEOUT: int = 30  # seconds
    MAX_RETRIES: int = 3
    BACKOFF_FACTOR: float = 2.0
    
    # Security
    ENCRYPTION_KEY: str = Field(..., min_length=32)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize database config with CONNECTOR_ prefix
        if self.DB_ENABLED:
            self.database_config = DatabaseConfig(
                DB_HOST=kwargs.get('CONNECTOR_DB_HOST', 'localhost'),
                DB_PORT=kwargs.get('CONNECTOR_DB_PORT', 5436),
                DB_NAME=kwargs.get('CONNECTOR_DB_NAME', 'connector_db'),
                DB_USER=kwargs.get('CONNECTOR_DB_USER', 'connector_user'),
                DB_PASSWORD=kwargs.get('CONNECTOR_DB_PASSWORD', 'connector_pass'),
                DB_ECHO=kwargs.get('CONNECTOR_DB_ECHO', False),
                DB_POOL_SIZE=kwargs.get('CONNECTOR_DB_POOL_SIZE', 20),
                DB_MAX_OVERFLOW=kwargs.get('CONNECTOR_DB_MAX_OVERFLOW', 10),
            )


def get_service_config() -> ServiceConfig:
    """Get service configuration."""
    import os
    from pydantic import ValidationError
    from pathlib import Path
    
    ENV_FILE = Path(__file__).parent.parent / ".env"
    
    try:
        config = ServiceConfig(_env_file=str(ENV_FILE) if ENV_FILE.exists() else None)
        return config
    except ValidationError as exc:
        print("\n=== Validation Error Details ===")
        for error in exc.errors():
            print(f"Field: {error['loc']}, Type: {error['type']}, Message: {error['msg']}")
        raise