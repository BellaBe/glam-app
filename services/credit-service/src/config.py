from functools import lru_cache
from pydantic import BaseModel, Field
from shared.utils.config_loader import merged_config, flatten_config
from shared.database import DatabaseConfig, create_database_config
import os


class CreditServiceConfig(BaseModel):
    # Service Identity (from shared + service YAML)
    service_name: str = Field(..., alias="service.name")
    service_version: str = Field(..., alias="service.version")
    environment: str
    debug: bool
    
    # API Configuration - BOTH PORTS
    api_host: str = Field(..., alias="api.host")
    api_port: int = Field(..., alias="api.port")                    # Internal/container port
    api_external_port: int = Field(..., alias="api.external_port")  # Local development port
    
    # Infrastructure (from shared YAML)
    infrastructure_nats_url: str = Field(..., alias="infrastructure.nats_url")
    infrastructure_redis_url: str = Field(..., alias="infrastructure.redis_url")
    
    # Database Configuration
    db_enabled: bool = Field(..., alias="database.enabled")
    
    # Logging (from shared YAML)
    logging_level: str = Field(..., alias="logging.level")
    logging_format: str = Field(..., alias="logging.format")
    logging_file_path: str = Field(..., alias="logging.file_path")
    
    # Rate Limiting (from shared YAML)
    rate_limiting_enabled: bool = Field(..., alias="rate_limiting.enabled")
    rate_limiting_window_seconds: int = Field(..., alias="rate_limiting.window_seconds")

    # Monitoring (from shared YAML)
    monitoring_metrics_enabled: bool = Field(..., alias="monitoring.metrics_enabled")
    monitoring_tracing_enabled: bool = Field(..., alias="monitoring.tracing_enabled")
    
    # Cache (service override of shared defaults)
    cache_ttl_seconds: int = Field(..., alias="cache.ttl_seconds")
    
    # Credit Configuration (service-specific)
    credit_trial_credits: int = Field(..., alias="credit.trial_credits")
    low_balance_threshold_percent: int = Field(..., alias="credit.low_balance_threshold_percent")


    @property
    def database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        cfg = create_database_config(prefix="CREDIT_")
        return cfg

    @property
    def effective_port(self) -> int:
        """
        Get the effective port to use based on environment.
        
        Logic:
        - Local development (not in Docker): use external_port
        - Docker/container environment: use internal port
        - Environment override: CREDIT_USE_EXTERNAL_PORT=true forces external_port
        """
        # Check if explicitly requested to use external port
        use_external = os.getenv("CREDIT_USE_EXTERNAL_PORT", "false").lower() == "true"
        
        # Check if running in container (common Docker environment variables)
        in_container = any([
            os.getenv("DOCKER_CONTAINER"),
            os.getenv("HOSTNAME", "").startswith("credit-service"),
            os.path.exists("/.dockerenv")
        ])
        
        if use_external or (not in_container and self.environment == "development"):
            return self.api_external_port
        else:
            return self.api_port


@lru_cache
def get_service_config() -> CreditServiceConfig:
    """Load and cache service configuration"""
    cfg_dict = merged_config("credit", env_prefix="CREDIT") 
    flattened = flatten_config(cfg_dict)
    return CreditServiceConfig(**flattened)
