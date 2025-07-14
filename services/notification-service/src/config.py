from functools import lru_cache
from typing import List, Optional
from pydantic import BaseModel, Field
from shared.config_loader import merged_config
from shared.database import DatabaseConfig, create_database_config


class NotificationConfig(BaseModel):
    # Service Identity (from shared + service YAML)
    service_name: str = Field(..., alias="service.name")
    service_version: str = Field(..., alias="service.version")
    environment: str
    debug: bool
    
    # API Configuration (from shared + service YAML)
    api_host: str = Field(..., alias="api.host")
    api_port: int = Field(..., alias="api.port")
    api_cors_origins: List[str] = Field(..., alias="api.cors_origins")
    
    # Infrastructure (from shared YAML)
    infrastructure_nats_url: str = Field(..., alias="infrastructure.nats_url")
    infrastructure_redis_url: str = Field(..., alias="infrastructure.redis_url")
    
    # Database (from shared YAML)
    database_host: str = Field(..., alias="database.host")
    database_port: int = Field(..., alias="database.port")
    database_pool_size: int = Field(..., alias="database.pool_size")
    database_max_overflow: int = Field(..., alias="database.max_overflow")
    database_echo: bool = Field(..., alias="database.echo")
    
    # Logging (from shared YAML)
    logging_level: str = Field(..., alias="logging.level")
    logging_format: str = Field(..., alias="logging.format")
    
    # Email Configuration (from shared + service YAML)
    email_primary_provider: str = Field(..., alias="email.primary_provider")
    email_fallback_provider: str = Field(..., alias="email.fallback_provider")
    email_from_domain: str = Field(..., alias="email.from_domain")
    email_smtp_port: int = Field(..., alias="email.smtp_port")
    
    # AWS (from shared YAML)
    aws_region: str = Field(..., alias="aws.region")
    
    # Rate Limiting (from shared + service YAML)
    rate_limiting_enabled: bool = Field(..., alias="rate_limiting.enabled")
    rate_limiting_window_seconds: int = Field(..., alias="rate_limiting.window_seconds")
    rate_limiting_per_hour: int = Field(..., alias="rate_limiting.per_hour")
    rate_limiting_per_day: int = Field(..., alias="rate_limiting.per_day")
    
    # Monitoring (from shared YAML)
    monitoring_metrics_enabled: bool = Field(..., alias="monitoring.metrics_enabled")
    monitoring_tracing_enabled: bool = Field(..., alias="monitoring.tracing_enabled")
    
    # Template Configuration (service-specific)
    template_max_size: int = Field(..., alias="template.max_size")
    template_render_timeout: int = Field(..., alias="template.render_timeout")
    
    # Retry Configuration (service-specific)
    retry_max_attempts: int = Field(..., alias="retry.max_attempts")
    retry_initial_delay_ms: int = Field(..., alias="retry.initial_delay_ms")
    retry_max_delay_ms: int = Field(..., alias="retry.max_delay_ms")
    
    # Bulk Email Configuration (service-specific)
    bulk_email_default_batch_size: int = Field(..., alias="bulk_email.default_batch_size")
    bulk_email_max_batch_size: int = Field(..., alias="bulk_email.max_batch_size")
    bulk_email_min_batch_size: int = Field(..., alias="bulk_email.min_batch_size")
    bulk_email_batch_delay_seconds: float = Field(..., alias="bulk_email.batch_delay_seconds")
    bulk_email_max_delay_seconds: float = Field(..., alias="bulk_email.max_delay_seconds")
    bulk_email_concurrent_batches: int = Field(..., alias="bulk_email.concurrent_batches")
    
    # External Services (env-only, optional)
    sendgrid_api_key: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from_address: Optional[str] = None
    email_from_name: Optional[str] = None
    
    @property
    def database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        return create_database_config(prefix="NOTIFICATION_")


@lru_cache
def get_service_config() -> NotificationConfig:
    """Load and cache service configuration"""
    cfg_dict = merged_config("notification", env_prefix="NOTIFICATION")
    return NotificationConfig(**cfg_dict)