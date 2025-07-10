# services/credit-service/src/config.py
"""
Credit service configuration management.

Follows the same pattern as notification service for consistency.
"""

from typing import Optional
from decimal import Decimal
from pydantic_settings import BaseSettings
from pydantic import Field

from shared.config.base import BaseServiceConfig


class CreditServiceConfig(BaseServiceConfig):
    """Configuration for credit service"""
    
    # Service identification
    SERVICE_NAME: str = Field(default="credit-service", env="SERVICE_NAME")
    SERVICE_PORT: int = Field(default=8015, env="SERVICE_PORT")
    
    # Redis for caching
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    CACHE_TTL_SECONDS: int = Field(default=60, env="CACHE_TTL_SECONDS")
    
    # Credit Configuration
    TRIAL_CREDITS: Decimal = Field(default=Decimal("100"), env="TRIAL_CREDITS")
    LOW_BALANCE_THRESHOLD_PERCENT: int = Field(default=20, env="LOW_BALANCE_THRESHOLD_PERCENT")
    
    # Order Credits
    ORDER_CREDIT_ENABLED: bool = Field(default=True, env="ORDER_CREDIT_ENABLED")
    ORDER_CREDIT_FIXED_AMOUNT: Decimal = Field(default=Decimal("10"), env="ORDER_CREDIT_FIXED_AMOUNT")
    ORDER_CREDIT_PERCENTAGE: Decimal = Field(default=Decimal("0.01"), env="ORDER_CREDIT_PERCENTAGE")
    ORDER_CREDIT_MINIMUM: Decimal = Field(default=Decimal("1"), env="ORDER_CREDIT_MINIMUM")
    
    # Plugin Status
    PLUGIN_STATUS_CACHE_TTL: int = Field(default=15, env="PLUGIN_STATUS_CACHE_TTL")
    PLUGIN_RATE_LIMIT_PER_MERCHANT: int = Field(default=100, env="PLUGIN_RATE_LIMIT_PER_MERCHANT")
    
    # Rate Limiting
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, env="RATE_LIMIT_WINDOW_SECONDS")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global config instance
_config: Optional[CreditServiceConfig] = None


def get_config() -> CreditServiceConfig:
    """Get or create config instance"""
    global _config
    if _config is None:
        _config = CreditServiceConfig()
    return _config


# For convenience
ServiceConfig = CreditServiceConfig