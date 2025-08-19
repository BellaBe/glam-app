import os
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field, model_validator

from shared.utils import load_root_env
from shared.utils.exceptions import ConfigurationError


class ServiceConfig(BaseModel):
    """Merchant service configuration"""

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    service_name: str = "merchant-service"
    service_version: str = "1.0.0"
    service_description: str = "Merchant management service"
    debug: bool = True

    environment: str = Field(..., alias="APP_ENV")
    api_host: str = "0.0.0.0"
    api_external_port: int = Field(..., alias="MERCHANT_API_EXTERNAL_PORT")

    database_enabled: bool = Field(..., alias="MERCHANT_DB_ENABLED")
    database_url: str = Field(..., alias="DATABASE_URL")

    logging_level: str = "INFO"
    logging_format: str = "json"
    logging_file_path: str = ""

    client_jwt_secret: str = Field(..., alias="CLIENT_JWT_SECRET")

    @property
    def nats_url(self) -> str:
        in_container = os.path.exists("/.dockerenv")
        return (
            "nats://nats:4222"
            if in_container or self.environment in ["development", "production"]
            else "nats://localhost:4222"
        )

    @property
    def redis_url(self) -> str:
        in_container = os.path.exists("/.dockerenv")
        return (
            "redis://redis:6379"
            if in_container or self.environment in ["development", "production"]
            else "redis://localhost:6379"
        )

    @property
    def api_port(self) -> int:
        in_container = os.path.exists("/.dockerenv")
        return 8000 if in_container else self.api_external_port

    @model_validator(mode="after")
    def _require_db_url_when_enabled(self):
        if self.database_enabled and not self.database_url:
            raise ValueError("database_enabled=true requires DATABASE_URL")
        return self


@lru_cache
def get_service_config() -> ServiceConfig:
    try:
        load_root_env()
        return ServiceConfig(**os.environ)  # type: ignore[typeddict-unknown-key]
    except Exception as e:
        raise ConfigurationError(
            f"Failed to load service configuration: {e}",
            config_key="merchant-service",
            expected_value="valid config",
        ) from e
