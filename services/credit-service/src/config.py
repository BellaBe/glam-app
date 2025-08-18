# services/credit-service/src/config.py
import os
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field, model_validator

from shared.utils import ConfigurationError, load_root_env


class ServiceConfig(BaseModel):
    """Credit service configuration"""

    model_config = ConfigDict(
        extra="ignore",
        case_sensitive=False,
        allow_population_by_field_name=True,
    )

    # Service identification
    service_name: str = "credit-service"
    service_version: str = "1.0.0"
    service_description: str = "Credit balance accounting service"
    debug: bool = Field(default=False, alias="DEBUG")

    # Environment
    environment: str = Field(..., alias="APP_ENV")
    api_external_port: int = Field(default=8002, alias="CREDIT_API_EXTERNAL_PORT")
    database_enabled: bool = Field(default=True, alias="CREDIT_DB_ENABLED")

    # Required secrets
    database_url: str = Field(..., alias="DATABASE_URL")
    client_jwt_secret: str = Field(..., alias="CLIENT_JWT_SECRET")
    internal_jwt_secret: str = Field(..., alias="INTERNAL_JWT_SECRET")

    # API configuration
    api_host: str = "0.0.0.0"

    # Business rules
    trial_credits: int = 500
    low_balance_threshold: int = 100

    # Logging
    logging_level: str = "INFO"
    logging_format: str = "json"

    @property
    def nats_url(self) -> str:
        """NATS URL for event system"""
        in_container = os.path.exists("/.dockerenv")
        if in_container or self.environment in ["development", "production"]:
            return "nats://nats:4222"
        return "nats://localhost:4222"

    @property
    def api_port(self) -> int:
        """Port based on environment"""
        in_container = os.path.exists("/.dockerenv")
        return 8000 if in_container else self.api_external_port

    @model_validator(mode="after")
    def validate_config(self):
        if self.database_enabled and not self.database_url:
            raise ValueError("DATABASE_URL required when database is enabled")
        return self


@lru_cache
def get_service_config() -> ServiceConfig:
    """Load configuration once"""
    try:
        load_root_env()
        return ServiceConfig(**os.environ)
    except Exception as e:
        raise ConfigurationError(f"Failed to load config: {e}", config_key="credit-service") from e
