# services/notification-service/src/config.py
from functools import lru_cache
from typing import List, Optional
from pydantic import ValidationError, Field, field_validator, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os
import json

# Import after loading env vars
from shared.database import DatabaseConfig, create_database_config


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # Goes up to glam-app/
ENV_FILE = BASE_DIR / ".env"


class EmailProviderConfig(BaseSettings):
    """Email provider configuration"""
    api_key: Optional[str] = None
    from_email: str = "noreply@glamyouup.com"
    from_name: str = "GlamYouUp"
    timeout_seconds: int = 30
    region: Optional[str] = None  # For SES
    host: Optional[str] = None    # For SMTP
    port: Optional[int] = None    # For SMTP
    username: Optional[str] = None # For SMTP
    password: Optional[str] = None # For SMTP

class RateLimitConfig(BaseSettings):
    """Rate limiting configuration"""
    rate_limit: str = "10/min"
    burst_limit: int = 20
    daily_limit: int = 1000
    batch_size: int = 100
    concurrent_batches: int = 5
    
class BulkEmailConfig(BaseModel):
    """Configuration for bulk email processing"""
    default_batch_size: int = 100
    max_batch_size: int = 1000
    min_batch_size: int = 1
    batch_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    concurrent_batches: int = 10  # Semaphore limit

class ServiceConfig(BaseSettings):
    """Notification service configuration"""
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_prefix="NOTIFICATION_",
        extra="ignore",
    )
    
    # Service Identity - using existing env vars
    SERVICE_NAME: str = Field(default="notification-service")
    SERVICE_VERSION: str = Field(default="1.0.0")
    
    # Environment - map from APP_ENV to ENVIRONMENT
    ENVIRONMENT: str = Field(default="development", alias="APP_ENV")
    DEBUG: bool = Field(default=True)
    
    # API Configuration - map from EXTERNAL_PORT to API_PORT
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8002, alias="EXTERNAL_PORT")
    
    # NATS Configuration - map from NATS_URL to NATS_SERVERS
    NATS_SERVERS: List[str] = Field(default_factory=lambda: ["nats://localhost:4222"])
    
    # Database
    DB_ENABLED: bool = Field(default=True)
    
    # Email Configuration - map from EMAIL_PROVIDER
    PRIMARY_PROVIDER: str = Field(default="sendgrid", alias="EMAIL_PROVIDER")
    FALLBACK_PROVIDER: str = Field(default="smtp")

    # Provider Configs
    SENDGRID_API_KEY: Optional[str] = Field(default=None)
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None)
    AWS_REGION: str = Field(default="us-east-1")
    SMTP_HOST: Optional[str] = Field(default=None)
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: Optional[str] = Field(default=None)
    SMTP_PASSWORD: Optional[str] = Field(default=None)
    
    # Rate Limiting - map from EMAIL_RATE_LIMIT_PER_HOUR/DAY
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    EMAIL_RATE_LIMIT_PER_HOUR: int = Field(default=100)
    EMAIL_RATE_LIMIT_PER_DAY: int = Field(default=1000)

    # Template Configuration
    MAX_TEMPLATE_SIZE: int = Field(default=1048576)  # 1MB
    TEMPLATE_RENDER_TIMEOUT: int = Field(default=30)

    # Retry Configuration - map from existing vars
    MAX_RETRY_ATTEMPTS: int = Field(default=3)
    INITIAL_RETRY_DELAY_MS: int = Field(default=1000)
    MAX_RETRY_DELAY_MS: int = Field(default=60000, validation_alias="RETRY_DELAY_SECONDS")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])
    ALLOWED_HOSTS: List[str] = Field(default_factory=list)
    
    @field_validator('NATS_SERVERS', mode='before')
    @classmethod
    def parse_nats_servers(cls, v):
        # If NATS_URL is provided, use it
        nats_url = os.getenv('NOTIFICATION_NATS_URL')
        if nats_url and not v:
            return [nats_url]
        # If it's a string that looks like JSON, parse it
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # If it's just a single URL, wrap it in a list
                return [v]
        return v or ["nats://localhost:4222"]
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v or ["*"]
    
    @field_validator('MAX_RETRY_DELAY_MS', mode='before')
    @classmethod
    def convert_retry_delay(cls, v, info):
        # If RETRY_DELAY_SECONDS is provided, convert to milliseconds
        if info.field_name == 'MAX_RETRY_DELAY_MS':
            retry_seconds = os.getenv('NOTIFICATION_RETRY_DELAY_SECONDS')
            if retry_seconds and not v:
                return int(retry_seconds) * 1000
        return v or 60000
    
    @property
    def database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        return create_database_config(prefix="NOTIFICATION_")
    
    @property
    def sendgrid_config(self) -> EmailProviderConfig:
        return EmailProviderConfig(
            api_key=self.SENDGRID_API_KEY,
            from_email=os.getenv('NOTIFICATION_EMAIL_FROM_ADDRESS', 'noreply@glamyouup.com'),
            from_name=os.getenv('NOTIFICATION_EMAIL_FROM_NAME', 'GlamYouUp')
        )
    
    @property
    def ses_config(self) -> EmailProviderConfig:
        return EmailProviderConfig(
            region=self.AWS_REGION,
            from_email=os.getenv('NOTIFICATION_EMAIL_FROM_ADDRESS', 'noreply@glamyouup.com'),
            from_name=os.getenv('NOTIFICATION_EMAIL_FROM_NAME', 'GlamYouUp')
        )
    
    @property
    def smtp_config(self) -> EmailProviderConfig:
        return EmailProviderConfig(
            host=self.SMTP_HOST,
            port=self.SMTP_PORT,
            username=self.SMTP_USERNAME,
            password=self.SMTP_PASSWORD,
            from_email=os.getenv('NOTIFICATION_EMAIL_FROM_ADDRESS', 'noreply@glamyouup.com'),
            from_name=os.getenv('NOTIFICATION_EMAIL_FROM_NAME', 'GlamYouUp')
        )
    
    @property
    def rate_limit_config(self) -> RateLimitConfig:
        return RateLimitConfig(
            daily_limit=self.EMAIL_RATE_LIMIT_PER_DAY,
            rate_limit=f"{self.EMAIL_RATE_LIMIT_PER_HOUR}/hour"
        )


@lru_cache()
def get_service_config() -> ServiceConfig:
    """Singleton accessor for service configuration."""
    try:
        # Debug what pydantic settings sees
        print("\n=== Environment Variables Debug ===")
        print(f"ENV_FILE exists: {ENV_FILE.exists()}")
        print(f"ENV_FILE path: {ENV_FILE}")
        
        # Show what env vars are available
        notification_vars = {k: v for k, v in os.environ.items() if k.startswith("NOTIFICATION_")}
        print(f"\nFound {len(notification_vars)} NOTIFICATION_ variables in environment")
        
        config = ServiceConfig()
        print("\nServiceConfig loaded successfully!")
        return config
    except ValidationError as exc:
        print("\n=== Validation Error Details ===")
        for error in exc.errors():
            print(f"Field: {error['loc']}, Type: {error['type']}, Message: {error['msg']}")
        
        raise