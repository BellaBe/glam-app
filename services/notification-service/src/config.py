# services/notification-service/src/config.py
from functools import lru_cache
from typing import List
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service configuration"""
    
    model_config = SettingsConfigDict(
        env_file="../../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="NOTIFICATION_",  # All env vars must start with NOTIFICATION_
        extra="ignore",  # Ignore any extra fields not defined in this class
    )
    
    # Database Configuration
    db_user: str
    db_password: str
    db_name: str
    db_port_external: int
    service_db_pool_size: int
    service_db_echo: bool
    
    # Service - no defaults, all required from .env
    service_name: str
    app_env: str
    external_port: int
    service_workers: int
    
    # NATS - no defaults
    nats_url: str
    
    # Redis - no defaults
    redis_url: str
    
    # Email Provider Settings - no defaults
    email_provider: str  # Should be set to "sendgrid" in .env
    email_from_address: str
    email_from_name: str
    
    # SendGrid Settings - required since using SendGrid
    sendgrid_api_key: str
    
    # Rate Limiting - no defaults
    email_rate_limit_per_hour: int
    email_rate_limit_per_day: int
    
    # Security - no defaults
    jwt_secret: str
    cors_origins: List[str]  # In .env, use JSON format: ["http://localhost:3000","https://example.com"]
    
    # Template Engine - no defaults
    template_engine: str  # Should be "jinja2" in .env
    
    # Retry Policy - no defaults
    max_retry_attempts: int
    retry_delay_seconds: int


# Create global settings instance
@lru_cache()
def get_settings() -> Settings:
    """Singleton accessor—import this wherever you need configuration."""
    try:
        print(Settings.model_validate({}).model_dump(mode="json"))
        return Settings() # type: ignore[call-arg]
    except ValidationError as exc:
        missing = (err["loc"][0] for err in exc.errors())  # may contain ints
        msg = ", ".join(str(name) for name in missing)     # <-- make them str
        raise RuntimeError(f"Missing required environment variables: {msg}") from exc
    
settings = get_settings()