# services/webhook-service/src/config.py
import os
from functools import lru_cache
from pydantic import BaseModel, Field, ConfigDict, model_validator
from shared.utils import load_root_env, ConfigurationError


class ServiceConfig(BaseModel):
    """Webhook service configuration"""
    model_config = ConfigDict(
        extra="ignore",
        case_sensitive=False,
        allow_population_by_field_name=True,
    )
    
    service_name: str = "webhook-service"
    service_version: str = "1.0.0"
    service_description: str = "Webhook management service"
    debug: bool = True 
    
    environment: str = Field(..., alias="APP_ENV")
    
    api_host: str = "0.0.0.0"
    api_external_port: int = Field(..., alias="WEBHOOK_API_EXTERNAL_PORT")
    
    database_enabled: int = Field(..., alias="WEBHOOK_DB_ENABLED")
    database_url: str = Field(..., alias="DATABASE_URL")
    
    logging_level: str = "INFO"
    logging_format: str = "json"
    logging_file_path: str = ""
    
    body_limit_bytes: int = 2097152 # 2MB default limit
    idempotency_ttl_seconds: int = 259200 # 72 hours default
    max_retries: int = 10
    retry_delay_seconds: int = 60 # Default since missing

    client_jwt_secret: str = Field(..., alias="CLIENT_JWT_SECRET")
    
    @property
    def nats_url(self) -> str:
        in_container = os.path.exists("/.dockerenv")
        if in_container or self.environment in ["development", "production"]:
            return "nats://nats:4222"
        return "nats://localhost:4222"
    
    @property
    def redis_url(self) -> str:
        in_container = os.path.exists("/.dockerenv")
        if in_container or self.environment in ["development", "production"]:
            return "redis://redis:6379"
        return "redis://localhost:6379"
    
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
    """Load config - fail if anything is missing"""
    try:
        load_root_env()
        return ServiceConfig(**os.environ)
    
    except Exception as e:
        raise ConfigurationError(
            f"Failed to load service configuration: {e}",
            config_key="webhook-service",
            expected_value="valid config"
        )