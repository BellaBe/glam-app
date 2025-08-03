# src/config.py
import os
from functools import lru_cache
from pydantic import BaseModel, Field
from shared.utils.config_loader import merged_config, flatten_config
from shared.database import create_database_config

class ConnectorServiceConfig(BaseModel):
    """Platform connector service configuration"""
    # Service Identity
    service_name: str = Field(..., alias="service.name")
    service_version: str = Field(..., alias="service.version")
    environment: str
    debug: bool
    
    # Infrastructure
    infrastructure_nats_url: str = Field(..., alias="infrastructure.nats_url")
    infrastructure_redis_url: str = Field(..., alias="infrastructure.redis_url")
    
    # Database (for tracking operations)
    db_enabled: bool = Field(True, alias="database.enabled")
    
    # Logging
    logging_level: str = Field(..., alias="logging.level")
    logging_format: str = Field(..., alias="logging.format")
    
    # Shopify Configuration
    shopify_api_version: str = Field("2024-01", alias="connector.shopify_api_version")
    shopify_bulk_poll_interval_sec: int = Field(10, alias="connector.shopify_bulk_poll_interval_sec")
    shopify_bulk_timeout_sec: int = Field(600, alias="connector.shopify_bulk_timeout_sec")
    shopify_rate_limit_per_sec: int = Field(4, alias="connector.shopify_rate_limit_per_sec")
    
    # Rate limiting
    rate_limit_window_sec: int = Field(60, alias="connector.rate_limit_window_sec")
    
    # Processing
    batch_size: int = Field(100, alias="connector.batch_size")
    max_retries: int = Field(3, alias="connector.max_retries")
    
    @property
    def database_config(self):
        """Get database configuration with CONNECTOR prefix"""
        return create_database_config("CONNECTOR_")
    
    @property
    def nats_servers(self) -> list[str]:
        return [self.infrastructure_nats_url]
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

@lru_cache
def get_connector_config() -> ConnectorServiceConfig:
    """Load and cache connector service configuration"""
    cfg_dict = merged_config("platform-connector", env_prefix="CONNECTOR")
    flattened = flatten_config(cfg_dict)
    return ConnectorServiceConfig(**flattened)

config = get_connector_config()