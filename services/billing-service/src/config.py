# services/billing-service/src/config.py
import os
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field, model_validator

from shared.utils import ConfigurationError, load_root_env


class ServiceConfig(BaseModel):
    """Billing service configuration"""

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
    )

    service_name: str = "billing-service"
    service_version: str = "1.0.0"
    service_description: str = "Billing and monetization service"
    debug: bool = True

    environment: str = Field(..., alias="APP_ENV")

    database_enabled: bool = True
    database_url: str = Field(..., alias="DATABASE_URL")
    
    client_jwt_secret: str = Field(..., alias="CLIENT_JWT_SECRET")
    internal_jwt_secret: str = Field(..., alias="INTERNAL_API_KEY")

    shopify_api_key: str = Field(..., alias="SHOPIFY_API_KEY")
    shopify_api_secret: str = Field(..., alias="SHOPIFY_API_SECRET")
    shopify_api_version: str = "2024-01"
    shopify_test_mode: bool = True


    logging_level: str = "INFO"
    logging_format: str = "json"
    logging_file_path: str = ""

    # Trial configuration
    trial_duration_days: int = 14
    trial_credits: int = 500

    # Credit packs configuration
    starter_pack_credits: int = 200
    starter_pack_price: str = "49.00"
    growth_pack_credits: int = 500
    growth_pack_price: str = "99.00"
    pro_pack_credits: int = 1000
    pro_pack_price: str = "179.00"

    @property
    def nats_url(self) -> str:
        """Dynamic NATS URL based on environment"""
        in_container = os.path.exists("/.dockerenv")
        if in_container or self.environment in ["dev", "prod"]:
            return "nats://nats:4222"
        return "nats://localhost:4222"

    @model_validator(mode="after")
    def _require_db_url_when_enabled(self):
        """Validate database URL is provided when database is enabled"""
        if self.database_enabled and not self.database_url:
            raise ValueError("database_enabled=true requires DATABASE_URL")
        return self


@lru_cache
def get_service_config() -> ServiceConfig:
    """Load config - fail fast if anything is missing"""
    try:
        load_root_env()
        return ServiceConfig(**os.environ)  # type: ignore[arg-type]
    except Exception as e:
        raise ConfigurationError(
            f"Failed to load service configuration: {e}", 
            config_key="billing-service", 
            expected_value="valid config"
        ) from e
