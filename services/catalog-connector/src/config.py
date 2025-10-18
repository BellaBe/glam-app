# services/platform-connector/src/config.py
import os
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field, model_validator

from shared.utils import ConfigurationError, load_root_env


class ServiceConfig(BaseModel):
    """Platform Connector configuration"""

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    # Service identification
    service_name: str = "platform-connector"
    service_version: str = "1.0.0"
    service_description: str = "E-commerce platform product data connector"
    debug: bool = Field(default=False, alias="DEBUG")

    # Required environment variables
    environment: str = Field(..., alias="APP_ENV")
    api_external_port: int = Field(default=8011, alias="CONNECTOR_API_EXTERNAL_PORT")

    # No database for this stateless service
    database_enabled: bool = False

    # Required secrets
    client_jwt_secret: str = Field(..., alias="CLIENT_JWT_SECRET")
    internal_jwt_secret: str = Field(..., alias="INTERNAL_JWT_SECRET")

    # Platform API configuration
    shopify_rate_limit_delay: float = Field(default=0.5, alias="SHOPIFY_RATE_LIMIT_DELAY")
    shopify_batch_size: int = Field(default=250, alias="SHOPIFY_BATCH_SIZE")
    shopify_max_retries: int = Field(default=3, alias="SHOPIFY_MAX_RETRIES")

    # WooCommerce settings
    woocommerce_batch_size: int = Field(default=100, alias="WOOCOMMERCE_BATCH_SIZE")

    # API configuration
    api_host: str = "0.0.0.0"

    # Logging
    logging_level: str = "INFO"
    logging_format: str = "json"

    # Retry configuration
    max_retry_attempts: int = Field(default=3, alias="CONNECTOR_MAX_RETRIES")
    retry_delay_seconds: float = Field(default=1.0, alias="CONNECTOR_RETRY_DELAY")

    # Token service config
    token_service_url: str = Field(..., alias="TOKEN_SERVICE_URL")
    token_service_timeout: int = Field(default=5, alias="TOKEN_SERVICE_TIMEOUT")
    token_service_retry_count: int = Field(default=3, alias="TOKEN_SERVICE_RETRY_COUNT")

    @property
    def nats_url(self) -> str:
        """NATS URL for event system"""
        in_container = os.path.exists("/.dockerenv")
        if in_container or self.environment in ["dev", "prod"]:
            return "nats://nats:4222"
        return "nats://localhost:4222"

    @property
    def api_port(self) -> int:
        """Port based on environment"""
        in_container = os.path.exists("/.dockerenv")
        return 8000 if in_container else self.api_external_port

    @model_validator(mode="after")
    def validate_config(self):
        # Stateless service doesn't need database
        if self.database_enabled:
            raise ValueError("Platform Connector should be stateless (database_enabled=false)")
        return self


@lru_cache
def get_service_config() -> ServiceConfig:
    """Load configuration once"""
    try:
        load_root_env()
        return ServiceConfig(**os.environ)
    except Exception as e:
        raise ConfigurationError(f"Failed to load config: {e}", config_key="platform-connector")
