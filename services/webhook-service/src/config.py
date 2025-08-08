import os
from functools import lru_cache
from typing import Optional, List
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
    
    nats_url: str = Field(..., alias="infrastructure.nats_url")
    redis_url: str = Field(..., alias="infrastructure.redis_url")
    
    logging_level: str = Field(..., alias="logging.level")
    logging_format: str = Field(..., alias="logging.format")
    logging_file_path: str = Field(..., alias="logging.file_path")
    
    monitoring_metrics_enabled: bool = Field(..., alias="monitoring.metrics_enabled")
    monitoring_tracing_enabled: bool = Field(..., alias="monitoring.tracing_enabled")
    
    rate_limiting_enabled: bool = Field(..., alias="rate_limiting.enabled")
    rate_limiting_window_seconds: int = Field(..., alias="rate_limiting.window_seconds")
    
    db_enabled: bool = Field(..., alias="database.enabled")
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    
    # Webhook specific config
    webhook_body_limit: int = Field(2097152, alias="webhook.body_limit_bytes")  # 2MB
    webhook_idempotency_ttl: int = Field(259200, alias="webhook.idempotency_ttl_seconds")  # 72h
    webhook_max_retries: int = Field(10, alias="webhook.max_retries")
    webhook_ip_allowlist_mode: str = Field("disabled", alias="webhook.ip_allowlist_mode")  # disabled/soft/hard
    webhook_shopify_ips: List[str] = Field(default_factory=list, alias="webhook.shopify_ips")
    
    # Shopify secrets
    shopify_api_secret: str = Field(..., alias="SHOPIFY_API_SECRET")
    shopify_api_secret_next: Optional[str] = Field(None, alias="SHOPIFY_API_SECRET_NEXT")
    
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
    cfg_dict = merged_config("webhook-service")
    flattened = flatten_config(cfg_dict)
    
    # Ensure raw env vars survive
    env_vars = ["DATABASE_URL", "SHOPIFY_API_SECRET", "SHOPIFY_API_SECRET_NEXT"]
    for var in env_vars:
        if var not in flattened and var in os.environ:
            flattened[var] = os.environ[var]
    
    return ServiceConfig(**flattened)


