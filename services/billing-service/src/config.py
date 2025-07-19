# services/billing-service/src/config.py
import os
from pathlib import Path
from pydantic import BaseModel, Field, SecretStr
from shared.config import merged_config, flatten_config
from shared.database import create_database_config


class BillingServiceConfig(BaseModel):
    """Billing service configuration from YAML + environment"""
    
    # From shared.yml
    environment: str = Field(alias="environment")
    debug: bool = Field(alias="debug")
    nats_url: str = Field(alias="infrastructure.nats_url")
    redis_url: str = Field(alias="infrastructure.redis_url")
    log_level: str = Field(alias="logging.level")
    metrics_enabled: bool = Field(alias="monitoring.metrics_enabled")
    
    # From service-specific YAML
    service_name: str = Field(alias="service.name")
    service_port: int = Field(alias="service.port", default=8016)
    external_port: int = Field(alias="api.external_port", default=8116)
    service_version: str = Field(alias="service.version", default="1.0.0")
    
    # Features from service YAML
    cache_enabled: bool = Field(alias="features.cache_enabled", default=True)
    max_retries: int = Field(alias="features.max_retries", default=3)
    timeout_seconds: int = Field(alias="features.timeout_seconds", default=30)
    
    # Billing business rules
    trial_period_days: int = Field(alias="billing.trial_period_days", default=14)
    max_trial_extensions: int = Field(alias="billing.max_trial_extensions", default=2)
    max_extension_days: int = Field(alias="billing.max_extension_days", default=30)
    
    # Shopify configuration
    shopify_api_version: str = Field(alias="shopify.api_version", default="2024-01")
    shopify_test_mode: bool = Field(alias="shopify.test_mode", default=False)
    
    # Secrets from environment (.env)
    shopify_api_key: SecretStr = Field(default=None)
    shopify_api_secret: SecretStr = Field(default=None)
    
    @property
    def database_url(self) -> str:
        prefix = "BILLING_SERVICE_"
        db_config = create_database_config(prefix)
        return db_config.database_url
    
    @property
    def nats_servers(self) -> list[str]:
        return [self.nats_url]
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"


def load_config() -> BillingServiceConfig:
    """Load configuration with proper path resolution"""
    service_dir = Path(__file__).parent.parent
    config_dir = service_dir.parent.parent / "config"
    
    raw_config = merged_config(
        service_name="billing-service",
        config_dir=str(config_dir),
        env_prefix="BILLING_SERVICE"
    )
    
    flat_config = flatten_config(raw_config)
    
    flat_config.update({
        "shopify_api_key": os.getenv("BILLING_SERVICE_SHOPIFY_API_KEY"),
        "shopify_api_secret": os.getenv("BILLING_SERVICE_SHOPIFY_API_SECRET"),
    })
    
    return BillingServiceConfig(**flat_config)