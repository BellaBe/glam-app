# services/analytics/src/config.py
import os
from functools import lru_cache
from pydantic import BaseModel, Field, ConfigDict, model_validator
from shared.utils import load_root_env, ConfigurationError

class ServiceConfig(BaseModel):
    """Analytics service configuration"""
    model_config = ConfigDict(
        extra="ignore",
        case_sensitive=False,
        allow_population_by_field_name=True,
    )
    
    # Service identification
    service_name: str = "analytics-service"
    service_version: str = "1.0.0"
    service_description: str = "Analytics and metrics aggregation service"
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Required environment variables
    environment: str = Field(..., alias="APP_ENV")
    api_external_port: int = Field(8117, alias="ANALYTICS_API_EXTERNAL_PORT")
    database_enabled: bool = Field(True, alias="ANALYTICS_DB_ENABLED")
    
    # Required secrets
    database_url: str = Field(..., alias="DATABASE_URL")
    client_jwt_secret: str = Field(..., alias="CLIENT_JWT_SECRET")
    internal_jwt_secret: str = Field(..., alias="INTERNAL_JWT_SECRET")
    
    # API configuration
    api_host: str = "0.0.0.0"
    
    # Aggregation settings
    aggregation_enabled: bool = Field(True, alias="ANALYTICS_AGGREGATION_ENABLED")
    hourly_aggregation_minute: int = 5  # Run at :05 past each hour
    daily_aggregation_hour: int = 0     # Run at midnight
    daily_aggregation_minute: int = 30  # Run at 00:30
    cleanup_retention_days: int = 90    # Keep raw events for 90 days
    
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
        return 8017 if in_container else self.api_external_port
    
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
        raise ConfigurationError(
            f"Failed to load config: {e}",
            config_key="analytics-service"
        )