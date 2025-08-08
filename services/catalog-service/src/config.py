import os
from functools import lru_cache
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from shared.utils.config_loader import merged_config, flatten_config

class ServiceConfig(BaseModel):
    """Service configuration from YAML + environment"""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")
    
    # Service Identity
    service_name: str = Field(..., alias="service.name")
    service_version: str = Field(..., alias="service.version")
    environment: str = Field(..., alias="environment")
    debug: bool = Field(False, alias="service.debug")
    
    # API Configuration - BOTH PORTS
    api_host: str = Field(..., alias="api.host")
    api_port: int = Field(..., alias="api.port")
    api_external_port: int = Field(..., alias="api.external_port")
    api_cors_origins: list[str] = Field(..., alias="api.cors_origins")
    
    # Infrastructure
    nats_url: str = Field(..., alias="infrastructure.nats_url")
    redis_url: str = Field(..., alias="infrastructure.redis_url")
    
    # Logging
    logging_level: str = Field(..., alias="logging.level")
    logging_format: str = Field(..., alias="logging.format")
    logging_file_path: str = Field(..., alias="logging.file_path")
    
    # Monitoring
    monitoring_metrics_enabled: bool = Field(..., alias="monitoring.metrics_enabled")
    monitoring_tracing_enabled: bool = Field(..., alias="monitoring.tracing_enabled")
    
    # Rate Limiting
    rate_limiting_enabled: bool = Field(..., alias="rate_limiting.enabled")
    rate_limiting_window_seconds: int = Field(..., alias="rate_limiting.window_seconds")
    
    # Database
    db_enabled: bool = Field(..., alias="database.enabled")
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    
    # API Authentication
    app_api_key: str = Field(..., alias="APP_API_KEY")
    
    # Cache TTLs
    cache_ttl_settings: int = Field(30, alias="cache.ttl_settings")  # 30 seconds
    cache_ttl_entitlements: int = Field(30, alias="cache.ttl_entitlements")  # 30 seconds
    
    @property
    def effective_api_port(self) -> int:
        in_container = os.path.exists("/.dockerenv")
        return self.api_port if in_container else self.api_external_port
    
    @model_validator(mode="after")
    def _require_db_url_when_enabled(self):
        if self.db_enabled and not self.database_url:
            raise ValueError("database.enabled=true requires DATABASE_URL")
        return self

@lru_cache
def get_service_config() -> ServiceConfig:
    """Load and cache service configuration"""
    cfg_dict = merged_config("catalog-service")
    flattened = flatten_config(cfg_dict)
    
    # Ensure raw DATABASE_URL and APP_API_KEY survive
    if "DATABASE_URL" not in flattened and "DATABASE_URL" in os.environ:
        flattened["DATABASE_URL"] = os.environ["DATABASE_URL"]
    if "APP_API_KEY" not in flattened and "APP_API_KEY" in os.environ:
        flattened["APP_API_KEY"] = os.environ["APP_API_KEY"]
    
    return ServiceConfig(**flattened)

# ================================================================
