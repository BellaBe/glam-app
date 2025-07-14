from functools import lru_cache
from pydantic import BaseModel, Field
from shared.config_loader import merged_config
from shared.database import DatabaseConfig, create_database_config


class CreditConfig(BaseModel):
    # Service Identity (from shared + service YAML)
    service_name: str = Field(..., alias="service.name")
    service_version: str = Field(..., alias="service.version")
    environment: str
    debug: bool
    
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
    
    # Cache (service override of shared defaults)
    cache_ttl_seconds: int = Field(..., alias="cache.ttl_seconds")
    
    # Credit Configuration (service-specific)
    credit_trial_credits: int = Field(..., alias="credit.trial_credits")
    credit_low_balance_threshold_percent: int = Field(..., alias="credit.low_balance_threshold_percent")
    
    # Order Credit Configuration (service-specific)
    order_credit_enabled: bool = Field(..., alias="order_credit.enabled")
    order_credit_fixed_amount: int = Field(..., alias="order_credit.fixed_amount")
    order_credit_percentage: int = Field(..., alias="order_credit.percentage")
    order_credit_minimum: int = Field(..., alias="order_credit.minimum")
    
    # Plugin Configuration (service-specific)
    plugin_status_cache_ttl: int = Field(..., alias="plugin.status_cache_ttl")
    plugin_rate_limit_per_merchant: int = Field(..., alias="plugin.rate_limit_per_merchant")
    
    @property
    def database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        return create_database_config(prefix="CREDIT_")


@lru_cache
def get_service_config() -> CreditConfig:
    """Load and cache service configuration"""
    cfg_dict = merged_config("credit", env_prefix="CREDIT")
    return CreditConfig(**cfg_dict)
