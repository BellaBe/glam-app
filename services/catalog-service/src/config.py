# services/catalog-service/src/config.py
import os
from functools import lru_cache
from pydantic import BaseModel, Field
from shared.config.loader import merged_config, flatten_config
from shared.database import create_database_config

class CatalogServiceConfig(BaseModel):
    """Catalog service configuration from YAML + environment"""
    # Service Identity
    service_name: str = Field(..., alias="service.name")
    service_version: str = Field(..., alias="service.version")
    environment: str
    debug: bool
    
    # API Configuration
    api_host: str = Field(..., alias="api.host")
    api_port: int = Field(..., alias="api.port")
    api_external_port: int = Field(..., alias="api.external_port")
    api_cors_origins: list = Field(..., alias="api.cors_origins")
    
    # Infrastructure
    infrastructure_nats_url: str = Field(..., alias="infrastructure.nats_url")
    infrastructure_redis_url: str = Field(..., alias="infrastructure.redis_url")
    
    # Database
    db_enabled: bool = Field(True, alias="database.enabled")
    
    # Logging
    logging_level: str = Field(..., alias="logging.level")
    logging_format: str = Field(..., alias="logging.format")
    
    # Catalog-specific features
    cache_enabled: bool = Field(True, alias="features.cache_enabled")
    max_retries: int = Field(3, alias="features.max_retries")
    
    # Image caching
    image_cache_dir: str = Field("/cache/images", alias="catalog.image_cache_dir")
    image_cache_ttl_hours: int = Field(72, alias="catalog.image_cache_ttl_hours")
    image_cache_max_size_gb: int = Field(100, alias="catalog.image_cache_max_size_gb")
    image_cache_type: str = Field("local", alias="catalog.image_cache_type")
    
    # Analysis
    analysis_timeout_sec: int = Field(300, alias="catalog.analysis_timeout_sec")
    analysis_batch_size: int = Field(32, alias="catalog.analysis_batch_size")
    
    # Sync operations
    sync_bulk_retry_max: int = Field(1, alias="catalog.sync_bulk_retry_max")
    
    # Recovery and reconciliation
    startup_recovery_enabled: bool = Field(True, alias="catalog.startup_recovery_enabled")
    reconciliation_interval_min: int = Field(10, alias="catalog.reconciliation_interval_min")
    reconciliation_batch_size: int = Field(100, alias="catalog.reconciliation_batch_size")
    
    # Idempotency
    enable_redis_idempotency: bool = Field(True, alias="catalog.enable_redis_idempotency")
    idempotency_ttl_hours: int = Field(24, alias="catalog.idempotency_ttl_hours")
    
    @property
    def database_config(self):
        """Get database configuration with CATALOG prefix"""
        return create_database_config("CATALOG_")
    
    @property
    def effective_port(self) -> int:
        """Get effective port based on environment"""
        in_container = any([
            os.getenv("DOCKER_CONTAINER"),
            os.getenv("HOSTNAME", "").startswith("catalog"),
            os.path.exists("/.dockerenv")
        ])
        return self.api_port if in_container else self.api_external_port
    
    @property
    def nats_servers(self) -> list[str]:
        return [self.infrastructure_nats_url]
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

@lru_cache
def get_catalog_config() -> CatalogServiceConfig:
    """Load and cache catalog service configuration"""
    cfg_dict = merged_config("catalog-service", env_prefix="CATALOG")
    flattened = flatten_config(cfg_dict)
    return CatalogServiceConfig(**flattened)

config = get_catalog_config()