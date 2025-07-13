# services/credit-service/src/config.py
"""
Credit service configuration management.

Follows the same pattern as notification service for consistency.
"""

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

class CreditServiceConfig(BaseSettings):
    """Configuration for credit service"""
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_prefix="CREDIT_",
        extra="ignore",
    )
    
    # Service identification
    SERVICE_NAME: str = Field(default="credit-service")
    SERVICE_VERSION: str = Field(default="1.0.0", env="SERVICE_VERSION")

    # Redis for caching
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    CACHE_TTL_SECONDS: int = Field(default=60, env="CACHE_TTL_SECONDS")
    
    # Credit Configuration
    TRIAL_CREDITS: int = Field(default=100, env="TRIAL_CREDITS")
    LOW_BALANCE_THRESHOLD_PERCENT: int = Field(default=20, env="LOW_BALANCE_THRESHOLD_PERCENT")
    
    # Order Credits
    ORDER_CREDIT_ENABLED: bool = Field(default=True, env="ORDER_CREDIT_ENABLED")
    ORDER_CREDIT_FIXED_AMOUNT: int = Field(default=10, env="ORDER_CREDIT_FIXED_AMOUNT")
    ORDER_CREDIT_PERCENTAGE: int = Field(default=1, env="ORDER_CREDIT_PERCENTAGE")
    ORDER_CREDIT_MINIMUM: int = Field(default=1, env="ORDER_CREDIT_MINIMUM")

    # Plugin Status
    PLUGIN_STATUS_CACHE_TTL: int = Field(default=15, env="PLUGIN_STATUS_CACHE_TTL")
    PLUGIN_RATE_LIMIT_PER_MERCHANT: int = Field(default=100, env="PLUGIN_RATE_LIMIT_PER_MERCHANT")
    
    # Rate Limiting
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=60, env="RATE_LIMIT_WINDOW_SECONDS")



@lru_cache()
def get_service_config() -> CreditServiceConfig:
    """Singleton accessor for service configuration."""
    try:
        # Debug what pydantic settings sees
        print("\n=== Environment Variables Debug ===")
        print(f"ENV_FILE exists: {ENV_FILE.exists()}")
        print(f"ENV_FILE path: {ENV_FILE}")
        
        # Show what env vars are available
        credit_vars = {k: v for k, v in os.environ.items() if k.startswith("CREDIT_")}
        print(f"\nFound {len(credit_vars)} CREDIT_ variables in environment")

        config = CreditServiceConfig()
        print("\nServiceConfig loaded successfully!")
        return config
    except ValidationError as exc:
        print("\n=== Validation Error Details ===")
        for error in exc.errors():
            print(f"Field: {error['loc']}, Type: {error['type']}, Message: {error['msg']}")
        
        raise