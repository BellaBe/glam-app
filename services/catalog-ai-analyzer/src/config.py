# services/catalog-ai-analyzer/src/config.py
import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from shared.utils import ConfigurationError, load_root_env


class ServiceConfig(BaseModel):
    """Catalog AI Analyzer service configuration"""

    model_config = ConfigDict(
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    # Service identification
    service_name: str = "catalog-ai-analyzer"
    service_version: str = "v1.0.0"
    service_description: str = "AI-powered catalog item analysis with MediaPipe and OpenAI Vision"
    debug: bool = Field(default=False, alias="DEBUG")

    # Required environment variables
    environment: str = Field(..., alias="APP_ENV")
    api_external_port: int = Field(default=8123, alias="CATALOG_AI_API_EXTERNAL_PORT")

    # No database for this service (stateless)
    database_enabled: bool = False

    # Required secrets (from .env)
    client_jwt_secret: str = Field(..., alias="CLIENT_JWT_SECRET")
    internal_jwt_secret: str = Field(..., alias="INTERNAL_JWT_SECRET")
    internal_api_keys: str = Field(..., alias="INTERNAL_API_KEYS")

    # OpenAI Configuration
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-vision-preview", alias="OPENAI_VISION_MODEL")
    openai_max_retries: int = Field(default=3, alias="OPENAI_MAX_RETRIES")
    openai_timeout_seconds: int = Field(default=30, alias="OPENAI_TIMEOUT_SECONDS")

    # MediaPipe Configuration
    model_path: str = Field(default="models/selfie_multiclass_256x256.tflite", alias="MEDIAPIPE_MODEL_PATH")

    # Processing Configuration
    max_concurrent_items: int = Field(default=5, alias="MAX_CONCURRENT_ITEMS")
    max_batch_size: int = Field(default=20, alias="MAX_BATCH_SIZE")
    image_download_timeout: int = Field(default=10, alias="IMAGE_DOWNLOAD_TIMEOUT")
    analysis_timeout_per_item: int = Field(default=30, alias="ANALYSIS_TIMEOUT_PER_ITEM")

    # Color extraction settings (from legacy)
    default_colors: int = Field(default=5, alias="DEFAULT_COLORS")
    sample_size: int = Field(default=20000, alias="COLOR_SAMPLE_SIZE")
    min_chroma: float = Field(default=5.0, alias="MIN_CHROMA")

    # API configuration
    api_host: str = "0.0.0.0"

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

    @model_validator(mode="after")
    def validate_config(self):
        # Validate model file exists
        model_path = Path(self.model_path)
        if not model_path.is_file():
            raise ValueError(f"Model file missing at {model_path}")
        return self


@lru_cache
def get_service_config() -> ServiceConfig:
    """Load configuration once"""
    try:
        load_root_env()
        return ServiceConfig(**os.environ)
    except Exception as e:
        raise ConfigurationError(f"Failed to load config: {e}", config_key="catalog-ai-analyzer")
