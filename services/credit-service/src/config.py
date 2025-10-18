# services/credit-service/src/config.py
import os
from functools import lru_cache
from pydantic import BaseModel, Field, ConfigDict, model_validator
from shared.utils import load_root_env
from shared.utils.exceptions import ConfigurationError

class ServiceConfig(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True, case_sensitive=False)

    service_name: str = "credit-service"
    service_version: str = "1.0.0"
    service_description: str = "Credit management service"
    debug: bool = Field(default=False, alias="DEBUG")

    environment: str = Field(..., alias="APP_ENV")
    database_enabled: bool = Field(default=True, alias="CREDIT_DB_ENABLED")
    database_url: str = Field(..., alias="DATABASE_URL")

    client_jwt_secret: str = Field(..., alias="CLIENT_JWT_SECRET")

    logging_level: str = "INFO"
    logging_format: str = "json"
    logging_file_path: str = ""

    low_balance_threshold: int = Field(default=100, alias="LOW_BALANCE_THRESHOLD")

    @property
    def nats_url(self) -> str:
        in_container = os.path.exists("/.dockerenv")
        if in_container or self.environment in ["dev", "prod", "production", "staging"]:
            return "nats://nats:4222"
        return "nats://localhost:4222"

    @model_validator(mode="after")
    def _require_db_url_when_enabled(self):
        if self.database_enabled and not self.database_url:
            raise ValueError("database_enabled=true requires DATABASE_URL")
        return self

@lru_cache
def get_service_config() -> ServiceConfig:
    try:
        load_root_env()
        return ServiceConfig(**os.environ)
    except Exception as e:
        raise ConfigurationError(
            f"Failed to load service configuration: {e}",
            config_key="credit-service",
            expected_value="valid config",
        ) from e
