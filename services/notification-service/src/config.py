# services/notification-service/src/config.py
import os
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from shared.utils import ConfigurationError, load_root_env


class ServiceConfig(BaseModel):
    """Notification service configuration"""

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    # Service identification
    service_name: str = "notification-service"
    service_version: str = "1.0.0"
    service_description: str = "Event-driven email notification service"
    debug: bool = Field(default=False, alias="DEBUG")

    # Required environment variables
    environment: str = Field(..., alias="APP_ENV")
    database_enabled: bool = Field(True, alias="NOTIFICATION_DB_ENABLED")

    # Required secrets
    database_url: str = Field(..., alias="DATABASE_URL")
    client_jwt_secret: str = Field(..., alias="CLIENT_JWT_SECRET")

    # Email provider configuration
    email_provider: Literal["sendgrid", "mailhog"] = Field("mailhog", alias="NOTIFICATION_EMAIL_PROVIDER")

    # SendGrid settings
    sendgrid_api_key: str = Field(default="", alias="SENDGRID_API_KEY")
    sendgrid_from_email: str = Field(default="noreply@glamyouup.com", alias="SENDGRID_FROM_EMAIL")
    sendgrid_from_name: str = Field(default="Glam You Up", alias="SENDGRID_FROM_NAME")
    sendgrid_sandbox_mode: bool = Field(False, alias="SENDGRID_SANDBOX_MODE")

    # Mailhog settings
    mailhog_smtp_host: str = Field(default="localhost", alias="MAILHOG_SMTP_HOST")
    mailhog_smtp_port: int = Field(default=1025, alias="MAILHOG_SMTP_PORT")

    # Template settings
    template_path: str = Field(default="/app/templates", alias="NOTIFICATION_TEMPLATE_PATH")
    template_cache_ttl: int = Field(default=300, alias="NOTIFICATION_CACHE_TTL")

    # Retry settings
    max_retries: int = Field(default=3, alias="NOTIFICATION_MAX_RETRIES")
    retry_delay: int = Field(default=60, alias="NOTIFICATION_RETRY_DELAY")

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
        return 8000 if in_container else self.api_external_port

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "prod"

    @model_validator(mode="after")
    def validate_config(self):
        if self.database_enabled and not self.database_url:
            raise ValueError("DATABASE_URL required when database is enabled")

        if self.email_provider == "sendgrid" and not self.sendgrid_api_key:
            raise ValueError("SENDGRID_API_KEY required when using SendGrid provider")

        # Use local template path in development
        if not os.path.exists("/.dockerenv") and self.environment == "local":
            import pathlib

            self.template_path = str(pathlib.Path(__file__).parent.parent / "templates")

        return self


@lru_cache
def get_service_config() -> ServiceConfig:
    """Load configuration once"""
    try:
        load_root_env()  # From shared package
        return ServiceConfig(**os.environ)  # type: ignore[arg-type]
    except Exception as e:
        raise ConfigurationError(f"Failed to load config: {e}", config_key="notification-service") from e
