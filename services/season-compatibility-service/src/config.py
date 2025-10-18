# services/season-compatibility/src/config.py
import os
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field, model_validator

from shared.utils import ConfigurationError, load_root_env


class ServiceConfig(BaseModel):
    """Service configuration with required shared package integration"""

    model_config = ConfigDict(
        extra="ignore",
        case_sensitive=False,
        allow_population_by_field_name=True,
    )

    # Service identification (required by shared package)
    service_name: str = "season-compatibility"
    service_version: str = "1.0.0"
    service_description: str = "Computes and stores seasonal color compatibility scores"
    debug: bool = Field(default=False, alias="DEBUG")

    # Required environment variables
    environment: str = Field(..., alias="APP_ENV")
    api_external_port: int = Field(default=8024, alias="SEASON_API_EXTERNAL_PORT")
    database_enabled: bool = Field(default=True, alias="SEASON_DB_ENABLED")

    # Required secrets (from .env)
    database_url: str = Field(..., alias="DATABASE_URL")
    internal_jwt_secret: str = Field(..., alias="INTERNAL_JWT_SECRET")

    # Service-specific auth
    recommendation_service_api_key: str = Field(..., alias="RECOMMENDATION_SERVICE_API_KEY")
    auth_enabled: bool = Field(default=True, alias="SEASON_SERVICE_AUTH_ENABLED")

    # API configuration
    api_host: str = "0.0.0.0"

    # Logging (used by shared package logger)
    logging_level: str = "INFO"
    logging_format: str = "json"

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
        raise ConfigurationError(f"Failed to load config: {e}", config_key="season-compatibility")
