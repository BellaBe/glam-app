# services/token-service/src/config.py

import os
from functools import lru_cache
from pydantic import BaseModel, Field, ConfigDict, model_validator
from shared.utils import load_root_env, ConfigurationError

class ServiceConfig(BaseModel):
    """Token Service configuration"""
    model_config = ConfigDict(
        extra="ignore",
        case_sensitive=False
    )
    
    # Service identification
    service_name: str = "token-service"
    service_version: str = "1.0.0"
    service_description: str = "Secure token storage and retrieval service"
    
    # Environment
    environment: str = Field(..., alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # API configuration
    api_host: str = "0.0.0.0"
    api_external_port: int = Field(default=8007, alias="TOKEN_API_EXTERNAL_PORT")
    
    # Database
    database_url: str = Field(..., alias="DATABASE_URL")
    database_enabled: bool = Field(default=True, alias="TOKEN_DB_ENABLED")
    
    # Security
    client_jwt_secret: str = Field(..., alias="CLIENT_JWT_SECRET")
    internal_api_keys: str = Field(..., alias="INTERNAL_JWT_SECRET")
    encryption_key: str = Field(..., alias="TOKEN_ENCRYPTION_KEY")
    encryption_key_id: str = Field(default="key_v1", alias="TOKEN_ENCRYPTION_KEY_ID")
    
    # Logging
    logging_level: str = Field(default="INFO", alias="LOGGING_LEVEL")
    
    @property
    def api_port(self) -> int:
        """Port based on environment"""
        in_container = os.path.exists("/.dockerenv")
        return 8000 if in_container else self.api_external_port
    
    @model_validator(mode="after")
    def validate_config(self):
        if not self.database_url:
            raise ValueError("DATABASE_URL is required")
        if not self.encryption_key:
            raise ValueError("TOKEN_ENCRYPTION_KEY is required")
        if len(self.encryption_key) < 32:
            raise ValueError("TOKEN_ENCRYPTION_KEY must be at least 32 characters")
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
            config_key="token-service"
        )