# services/merchant-service/src/config.py
import os
from functools import lru_cache
from pydantic import BaseModel, Field
from shared.config.loader import merged_config, flatten_config
from shared.database import create_database_config

class MerchantServiceConfig(BaseModel):
    """Service configuration from YAML + environment"""
    # Service Identity (from shared + service YAML)
    service_name: str = Field(..., alias="service.name")
    service_version: str = Field(..., alias="service.version")
    environment: str
    debug: bool
    
    # API Configuration - BOTH PORTS
    api_host: str = Field(..., alias="api.host")
    api_port: int = Field(..., alias="api.port")                    # Container port
    api_external_port: int = Field(..., alias="api.external_port")  # Local dev port
    api_cors_origins: list = Field(..., alias="api.cors_origins")
    
    # Infrastructure (from shared YAML)
    infrastructure_nats_url: str = Field(..., alias="infrastructure.nats_url")
    infrastructure_redis_url: str = Field(..., alias="infrastructure.redis_url")
    
    # Database Configuration
    db_enabled: bool = Field(..., alias="database.enabled")
    
    # Logging (from shared YAML)
    logging_level: str = Field(..., alias="logging.level")
    logging_format: str = Field(..., alias="logging.format")
    
    # Features (service-specific)
    cache_enabled: bool = Field(..., alias="features.cache_enabled", default=True)
    max_retries: int = Field(..., alias="features.max_retries", default=3)
    
    # Shopify Integration
    shopify_api_version: str = Field(default="2024-01")
    shopify_rate_limit_requests: int = Field(default=40)
    shopify_rate_limit_window: int = Field(default=2)
    
    # Security
    jwt_secret_key: str = Field(default="your-secret-key")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_minutes: int = Field(default=60)
    encryption_key: str = Field(default="your-encryption-key")
    
    @property
    def database_config(self):
        """Get database configuration with service prefix"""
        return create_database_config("MERCHANT_")
    
    @property
    def effective_port(self) -> int:
        """Get effective port based on environment"""
        # Check if running in container
        in_container = any([
            os.getenv("DOCKER_CONTAINER"),
            os.getenv("HOSTNAME", "").startswith("merchant-service"),
            os.path.exists("/.dockerenv")
        ])
        
        if in_container:
            return self.api_port
        else:
            return self.api_external_port
    
    @property
    def nats_servers(self) -> list[str]:
        return [self.infrastructure_nats_url]
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

@lru_cache
def get_service_config() -> MerchantServiceConfig:
    """Load and cache service configuration"""
    cfg_dict = merged_config("merchant-service", env_prefix="MERCHANT")
    flattened = flatten_config(cfg_dict)
    return MerchantServiceConfig(**flattened)
