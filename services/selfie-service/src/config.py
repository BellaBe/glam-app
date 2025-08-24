# services/selfie-service/src/config.py
import os
from functools import lru_cache
from pydantic import BaseModel, Field, ConfigDict, model_validator
from shared.utils import load_root_env, ConfigurationError

class ServiceConfig(BaseModel):
    """Selfie service configuration"""
    model_config = ConfigDict(
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )
    
    # Service identification
    service_name: str = "selfie-service"
    service_version: str = "1.0.0"
    service_description: str = "Selfie validation and analysis service"
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Environment
    environment: str = Field(..., alias="APP_ENV")
    api_external_port: int = Field(default=8026, alias="SELFIE_API_EXTERNAL_PORT")
    database_enabled: bool = Field(default=True, alias="SELFIE_DB_ENABLED")
    
    # Secrets
    database_url: str = Field(..., alias="DATABASE_URL")
    client_jwt_secret: str = Field(..., alias="CLIENT_JWT_SECRET")
    internal_jwt_secret: str = Field(..., alias="INTERNAL_JWT_SECRET")
    global_dedup_secret: str = Field(..., alias="GLOBAL_DEDUP_SECRET")
    
    # AI Analyzer
    ai_analyzer_url: str = Field(..., alias="AI_ANALYZER_URL")
    ai_analyzer_api_key: str = Field(..., alias="AI_ANALYZER_API_KEY")
    ai_analyzer_timeout = 25
    
    # Image processing limits
    max_upload_size = 10_485_760  # 10MB
    max_image_pixels = 12_000_000  # 12MP
    min_image_dimension = 480

    # Image quality thresholds
    min_blur_score = 100.0
    min_exposure = 60
    max_exposure = 200
    min_face_area_ratio = 0.07

    # Analyzer image settings
    analyzer_max_side = 1280
    analyzer_quality_high = 90
    analyzer_quality_medium = 85
    analyzer_max_size = 1_500_000  # 1.5MB
    min_face_width_after_resize = 300

    # Deduplication
    dedup_window_days = 30

    # Cleanup sweeper
    sweeper_interval_seconds = 45

    # API settings
    api_host = "0.0.0.0"
    logging_level = "INFO"

    # CORS origins
    cors_origins = [
        "https://*.myshopify.com",
        "https://*.shopify.com"
    ]
    
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
        return 8000 if in_container else self.api_external_port
    
    @model_validator(mode="after")
    def validate_config(self):
        if self.database_enabled and not self.database_url:
            raise ValueError("DATABASE_URL required when database is enabled")
        if not self.global_dedup_secret:
            raise ValueError("GLOBAL_DEDUP_SECRET is required")
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
            config_key="selfie-service"
        )