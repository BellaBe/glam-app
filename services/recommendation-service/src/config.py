# services/recommendation-service/src/config.py
import os
from functools import lru_cache
from pydantic import BaseModel, Field, ConfigDict, model_validator
from shared.utils import load_root_env, ConfigurationError


class ServiceConfig(BaseModel):
    """Recommendation Service configuration"""
    model_config = ConfigDict(
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )
    
    # Service identification
    service_name: str = "recommendation-service"
    service_version: str = "1.0.0"
    service_description: str = "Orchestrates product recommendations based on seasonal color analysis"
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Required environment variables
    environment: str = Field(..., alias="APP_ENV")
    api_external_port: int = Field(default=8125, alias="RECOMMENDATION_API_EXTERNAL_PORT")
    database_enabled: bool = Field(default=True, alias="RECOMMENDATION_DB_ENABLED")
    
    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    
    # Auth secrets
    client_jwt_secret: str = Field(..., alias="CLIENT_JWT_SECRET")
    internal_jwt_secret: str = Field(..., alias="INTERNAL_JWT_SECRET")
    internal_api_keys: str = Field(..., alias="INTERNAL_API_KEYS")
    
    # Season Compatibility Service
    season_compatibility_url: str = Field(
        default="http://season-compatibility-service:8000",
        alias="SEASON_COMPATIBILITY_URL"
    )
    season_compatibility_api_key: str = Field(..., alias="SEASON_COMPATIBILITY_API_KEY")
    season_compatibility_timeout: int = Field(default=5, alias="SEASON_COMPATIBILITY_TIMEOUT")
    
    # API configuration
    api_host: str = "0.0.0.0"
    min_score: float = 0.7
    
    # Logging
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
        return 8025 if in_container else self.api_external_port
    
    @model_validator(mode="after")
    def validate_config(self):
        if self.database_enabled and not self.database_url:
            raise ValueError("DATABASE_URL required when database is enabled")
        if not self.season_compatibility_api_key:
            raise ValueError("SEASON_COMPATIBILITY_API_KEY is required")
        return self


@lru_cache
def get_service_config() -> ServiceConfig:
    """Load configuration once"""
    try:
        load_root_env()
        return ServiceConfig(**os.environ)
    except Exception as e:
        raise ConfigurationError(
            f"Failed to load config: {e}",
            config_key="recommendation-service"
        )