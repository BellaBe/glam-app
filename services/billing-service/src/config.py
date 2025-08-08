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
    
    # Rate limiting
    rate_limiting_enabled: bool = Field(..., alias="rate_limiting.enabled")
    rate_limiting_window_seconds: int = Field(..., alias="rate_limiting.window_seconds")
    
    # Database
    db_enabled: bool = Field(..., alias="database.enabled")
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    
    # Authentication
    billing_api_key: str = Field(..., alias="BILLING_API_KEY")
    billing_admin_api_key: str = Field(..., alias="BILLING_ADMIN_API_KEY")
    
    # Shopify Configuration
    app_handle: str = Field(..., alias="APP_HANDLE")
    shopify_managed_checkout_base: str = Field(..., alias="SHOPIFY_MANAGED_CHECKOUT_BASE")
    allowed_return_domains: List[str] = Field(..., alias="ALLOWED_RETURN_DOMAINS")
    
    # Trial Configuration
    default_trial_days: int = Field(14, alias="DEFAULT_TRIAL_DAYS")
    trial_grace_hours: int = Field(0, alias="TRIAL_GRACE_HOURS")
    
    # Cache Configuration
    idempotency_ttl_hours: int = Field(24, alias="IDEMPOTENCY_TTL_HOURS")
    entitlements_cache_ttl_seconds: int = Field(30, alias="ENTITLEMENTS_CACHE_TTL_SECONDS")
    reconciliation_cache_ttl_seconds: int = Field(60, alias="RECONCILIATION_CACHE_TTL_SECONDS")
    
    # Rate Limiting
    shopify_rate_limit_points_per_second: int = Field(2, alias="SHOPIFY_RATE_LIMIT_POINTS_PER_SECOND")
    
    @property
    def effective_api_port(self) -> int:
        in_container = os.path.exists("/.dockerenv")
        return self.api_port if in_container else self.api_external_port
    
    @model_validator(mode="after")
    def _require_db_url_when_enabled(self):
        if self.db_enabled and not self.database_url:
            raise ValueError("database.enabled=true requires DATABASE_URL")
        return self
    
    @model_validator(mode="after")
    def _parse_allowed_domains(self):
        if isinstance(self.allowed_return_domains, str):
            self.allowed_return_domains = [d.strip() for d in self.allowed_return_domains.split(",")]
        return self

@lru_cache
def get_service_config() -> ServiceConfig:
    """Load and cache service configuration"""
    cfg_dict = merged_config("billing-service")
    flattened = flatten_config(cfg_dict)
    
    # Ensure environment variables survive
    env_vars = [
        "DATABASE_URL", "BILLING_API_KEY", "BILLING_ADMIN_API_KEY",
        "APP_HANDLE", "SHOPIFY_MANAGED_CHECKOUT_BASE", "ALLOWED_RETURN_DOMAINS",
        "DEFAULT_TRIAL_DAYS", "TRIAL_GRACE_HOURS", "IDEMPOTENCY_TTL_HOURS",
        "ENTITLEMENTS_CACHE_TTL_SECONDS", "RECONCILIATION_CACHE_TTL_SECONDS",
        "SHOPIFY_RATE_LIMIT_POINTS_PER_SECOND"
    ]
    
    for var in env_vars:
        if var not in flattened and var in os.environ:
            flattened[var] = os.environ[var]
    
    return ServiceConfig(**flattened)

