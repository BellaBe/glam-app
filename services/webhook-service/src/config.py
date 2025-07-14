from functools import lru_cache
from typing import Optional
from pydantic import BaseModel, Field
from shared.config_loader import merged_config
from shared.database import DatabaseConfig, create_database_config


class WebhookConfig(BaseModel):
    # Service Identity (from shared + service YAML)
    service_name: str = Field(..., alias="service.name")
    service_version: str = Field(..., alias="service.version")
    environment: str
    debug: bool
    
    # API Configuration (from shared + service YAML)
    api_host: str = Field(..., alias="api.host")
    api_port: int = Field(..., alias="api.port")
    api_workers: int = Field(..., alias="api.workers")
    
    # Infrastructure (from shared YAML)
    infrastructure_nats_url: str = Field(..., alias="infrastructure.nats_url")
    infrastructure_redis_url: str = Field(..., alias="infrastructure.redis_url")
    
    # Database (from shared YAML)
    database_host: str = Field(..., alias="database.host")
    database_port: int = Field(..., alias="database.port")
    database_pool_size: int = Field(..., alias="database.pool_size")
    database_echo: bool = Field(..., alias="database.echo")
    
    # Logging (from shared YAML)
    logging_level: str = Field(..., alias="logging.level")
    logging_format: str = Field(..., alias="logging.format")
    
    # Rate Limiting (from shared YAML)
    rate_limiting_enabled: bool = Field(..., alias="rate_limiting.enabled")
    rate_limiting_window_seconds: int = Field(..., alias="rate_limiting.window_seconds")
    
    # Monitoring (from shared YAML)
    monitoring_metrics_enabled: bool = Field(..., alias="monitoring.metrics_enabled")
    
    # Webhook Configuration (service-specific)
    webhook_max_payload_size_mb: int = Field(..., alias="webhook.max_payload_size_mb")
    webhook_dedup_ttl_hours: int = Field(..., alias="webhook.dedup_ttl_hours")
    
    # Circuit Breaker Configuration (service-specific)
    circuit_breaker_failure_threshold: int = Field(..., alias="circuit_breaker.failure_threshold")
    circuit_breaker_recovery_timeout: int = Field(..., alias="circuit_breaker.recovery_timeout")
    
    # External Services (env-only, optional)
    shopify_webhook_secret: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    
    @property
    def database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        return create_database_config(prefix="WEBHOOK_")


@lru_cache
def get_service_config() -> WebhookConfig:
    """Load and cache service configuration"""
    cfg_dict = merged_config("webhook", env_prefix="WEBHOOK")
    return WebhookConfig(**cfg_dict)