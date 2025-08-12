import os
from functools import lru_cache
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from shared.utils.config_loader import merged_config, flatten_config
from shared.utils.exceptions import ConfigurationError

class ServiceConfig(BaseModel):
    """Service configuration from YAML + environment"""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    
    # Service Identity
    service_name: str = Field(..., alias="service.name")
    service_version: str = Field(..., alias="service.version")
    service_description: str = Field(..., alias="service.description")
    debug: bool = Field(..., alias="service.debug")
    
    # Environment - from env
    environment: str = Field(..., alias="APP_ENV")
    
    # API Configuration
    api_host: str = Field(..., alias="api.host")
    api_external_port: int = Field(..., alias="MERCHANT_API_EXTERNAL_PORT")
    api_cors_origins: list[str] = Field(..., alias="api.cors_origins")
    
    # Database
    database_enabled: bool = Field(..., alias="MERCHANT_DB_ENABLED")
    database_url: str = Field(..., alias="DATABASE_URL")

    # Logging
    logging_level: str = Field(..., alias="logging.level")
    logging_format: str = Field(..., alias="logging.format")
    logging_file_path: str = Field(..., alias="logging.file_path")
    
    # Monitoring
    monitoring_metrics_enabled: bool = Field(..., alias="monitoring.metrics_enabled")
    monitoring_tracing_enabled: bool = Field(..., alias="monitoring.tracing_enabled")
    
    # Rate limiting
    rate_limiting_enabled: bool = Field(..., alias="rate_limiting.enabled")
    rate_limiting_window_seconds: int = Field(..., alias="rate_limiting.window_seconds")
    
    # Internal Authentication
    internal_jwt_secret: str = Field(..., alias="INTERNAL_JWT_KEY")
    
    # Computed properties
    @property
    def nats_url(self) -> str:
        in_container = os.path.exists("/.dockerenv")
        if in_container or self.environment in ["development", "production"]:
            return "nats://nats:4222"
        return "nats://localhost:4222"
    
    @property
    def redis_url(self) -> str:
        in_container = os.path.exists("/.dockerenv")
        if in_container or self.environment in ["development", "production"]:
            return "redis://redis:6379"
        return "redis://localhost:6379"
    
    @property
    def api_port(self) -> int:
        in_container = os.path.exists("/.dockerenv")
        return 8000 if in_container else self.api_external_port

    @model_validator(mode="after")
    def _require_db_url_when_enabled(self):
        if self.database_enabled and not self.database_url:
            raise ValueError("database_enabled=true requires DATABASE_URL")
        return self


@lru_cache
def get_service_config() -> ServiceConfig:
    """Load and cache service configuration"""
    try:
        # Load YAML + all env vars
        cfg_dict = merged_config("merchant-service")
        flattened = flatten_config(cfg_dict)
        return ServiceConfig(**flattened)
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        raise ConfigurationError(
            f"Failed to load service configuration: {e}", 
            config_key="merchant-service", 
            expected_value="valid config"
        )