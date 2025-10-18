# services/catalog-service/src/config.py
import os
from functools import lru_cache
from pydantic import BaseModel, Field, ConfigDict, model_validator
from shared.utils import load_root_env, ConfigurationError

class ServiceConfig(BaseModel):
    """Catalog service configuration with required shared package integration"""
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )
    
    # Service identification (required by shared package)
    service_name: str = "catalog-service"
    service_version: str = "1.0.0"
    service_description: str = "Product catalog synchronization and AI analysis orchestration"
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Required environment variables
    environment: str = Field(..., alias="APP_ENV")
    api_external_port: int = Field(..., alias="CATALOG_API_EXTERNAL_PORT")
    database_enabled: bool = Field(default=True, alias="CATALOG_DB_ENABLED")
    
    # Required secrets (from .env)
    database_url: str = Field(..., alias="DATABASE_URL")
    client_jwt_secret: str = Field(..., alias="CLIENT_JWT_SECRET")
    internal_jwt_secret: str = Field(..., alias="INTERNAL_JWT_SECRET")
    
    # Redis for progress tracking
    redis_enabled: bool = Field(default=True, alias="CATALOG_REDIS_ENABLED")
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    
    # API configuration
    api_host: str = "0.0.0.0"
    
    # Sync configuration
    sync_batch_size: int = Field(default=100, alias="CATALOG_SYNC_BATCH_SIZE")
    sync_progress_ttl: int = Field(default=3600, alias="CATALOG_SYNC_PROGRESS_TTL")
    
    # Logging (used by shared package logger)
    logging_level: str = "INFO"
    logging_format: str = "json"
    
    @property
    def nats_url(self) -> str:
        """NATS URL for event system"""
        in_container = os.path.exists("/.dockerenv")
        if in_container or self.environment in ["dev", "prod"]:
            return "nats://nats:4222"
        return "nats://localhost:4222"
    
    @property
    def api_port(self) -> int:
        """Port based on environment"""
        in_container = os.path.exists("/.dockerenv")
        return 8000 if in_container else self.api_external_port
    
    @model_validator(mode="after")
    def validate_config(self):
        if self.database_enabled and not self.database_url:
            raise ValueError("DATABASE_URL required when database is enabled")
        if self.redis_enabled and not self.redis_url:
            raise ValueError("REDIS_URL required when Redis is enabled")
        return self

@lru_cache
def get_service_config() -> ServiceConfig:
    """Load configuration once"""
    try:
        load_root_env()  # From shared package, loads root .env
        return ServiceConfig(**os.environ)
    except Exception as e:
        raise ConfigurationError(
            f"Failed to load config: {e}",
            config_key="catalog-service"
        )