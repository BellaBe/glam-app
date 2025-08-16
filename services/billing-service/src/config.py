# services/billing-service/src/config.py
import os
from functools import lru_cache
from pydantic import BaseModel, Field, ConfigDict, model_validator
from shared.utils import load_root_env, ConfigurationError


class ServiceConfig(BaseModel):
    """Billing service configuration"""
    model_config = ConfigDict(
        extra="ignore",
        case_sensitive=False,
        validate_by_name=True,
    )
    
    # Service basics with defaults
    service_name: str = "billing-service"
    service_version: str = "1.0.0"
    service_description: str = "Billing service for trial and credit pack management"
    debug: bool = True
    
    # Required from environment
    environment: str = Field(..., alias="APP_ENV")
    api_external_port: int = Field(..., alias="BILLING_API_EXTERNAL_PORT")
    database_enabled: bool = Field(..., alias="BILLING_DB_ENABLED")
    
    # Secrets from .env (required)
    database_url: str = Field(..., alias="DATABASE_URL")
    client_jwt_secret: str = Field(..., alias="CLIENT_JWT_SECRET")
    internal_jwt_secret: str = Field(..., alias="INTERNAL_JWT_SECRET")
    
    # Shopify configuration
    shopify_api_key: str = Field(..., alias="SHOPIFY_API_KEY")
    shopify_api_secret: str = Field(..., alias="SHOPIFY_API_SECRET")
    shopify_api_version: str = Field(default="2024-01", alias="SHOPIFY_API_VERSION")
    
    # Optional with defaults
    api_host: str = "0.0.0.0"
    logging_level: str = "INFO"
    logging_format: str = "json"
    
    # Trial configuration
    trial_duration_days: int = 14
    trial_credits: int = 500
    
    # Credit packs configuration
    small_pack_credits: int = 100
    small_pack_price: str = "9.99"
    medium_pack_credits: int = 500
    medium_pack_price: str = "39.99"
    large_pack_credits: int = 1000
    large_pack_price: str = "69.99"
    
    # Purchase expiry
    pending_purchase_expiry_hours: int = 24
    
    @property
    def nats_url(self) -> str:
        """Dynamic NATS URL based on environment"""
        in_container = os.path.exists("/.dockerenv")
        if in_container or self.environment in ["development", "production"]:
            return "nats://nats:4222"
        return "nats://localhost:4222"
    
    @property
    def redis_url(self) -> str:
        """Dynamic Redis URL based on environment"""
        in_container = os.path.exists("/.dockerenv")
        if in_container or self.environment in ["development", "production"]:
            return "redis://redis:6379"
        return "redis://localhost:6379"
    
    @property
    def api_port(self) -> int:
        """Internal port (8000 in container, external port locally)"""
        in_container = os.path.exists("/.dockerenv")
        return 8000 if in_container else self.api_external_port
    
    @model_validator(mode="after")
    def _require_db_url_when_enabled(self):
        """Validate database URL is provided when database is enabled"""
        if self.database_enabled and not self.database_url:
            raise ValueError("database_enabled=true requires DATABASE_URL")
        return self


@lru_cache
def get_service_config() -> ServiceConfig:
    """Load config - fail fast if anything is missing"""
    try:
        # Load .env file (for local development)
        load_root_env()
        
        # Create config from environment variables
        return ServiceConfig(**os.environ)
    except Exception as e:
        raise ConfigurationError(
            f"Failed to load service configuration: {e}",
            config_key="billing-service",
            expected_value="valid config"
        )


