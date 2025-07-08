# services/webhook-service/src/config.py
"""
Webhook service configuration management.

Follows the same pattern as notification service for consistency.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

from shared.config.base import BaseServiceConfig


class WebhookServiceConfig(BaseServiceConfig):
    """Configuration for webhook service"""
    
    # Service identification
    SERVICE_NAME: str = Field(default="webhook-service", env="SERVICE_NAME")
    SERVICE_PORT: int = Field(default=8012, env="SERVICE_PORT")
    
    # Webhook-specific settings
    SHOPIFY_WEBHOOK_SECRET: str = Field(..., env="SHOPIFY_WEBHOOK_SECRET")
    SHOPIFY_API_VERSION: str = Field(default="2024-01", env="SHOPIFY_API_VERSION")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(default=None, env="STRIPE_WEBHOOK_SECRET")
    
    # Redis for deduplication
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    DEDUP_TTL_HOURS: int = Field(default=24, env="DEDUP_TTL_HOURS")
    
    # Performance settings
    MAX_PAYLOAD_SIZE_MB: int = Field(default=10, env="MAX_PAYLOAD_SIZE_MB")
    WEBHOOK_TIMEOUT_SECONDS: int = Field(default=30, env="WEBHOOK_TIMEOUT_SECONDS")
    
    # Circuit breaker settings
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = Field(default=5, env="CIRCUIT_BREAKER_FAILURE_THRESHOLD")
    CIRCUIT_BREAKER_TIMEOUT_SECONDS: int = Field(default=60, env="CIRCUIT_BREAKER_TIMEOUT_SECONDS")
    CIRCUIT_BREAKER_WINDOW_SECONDS: int = Field(default=30, env="CIRCUIT_BREAKER_WINDOW_SECONDS")
    
    # Dead letter queue settings
    DLQ_MAX_RETRIES: int = Field(default=5, env="DLQ_MAX_RETRIES")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global config instance
_config: Optional[WebhookServiceConfig] = None


def get_config() -> WebhookServiceConfig:
    """Get or create config instance"""
    global _config
    if _config is None:
        _config = WebhookServiceConfig()
    return _config


# For convenience
ServiceConfig = WebhookServiceConfig