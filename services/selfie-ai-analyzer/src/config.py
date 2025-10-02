# services/selfie-ai-analyzer/src/config.py
import os
from functools import lru_cache
from pydantic import BaseModel, Field, ConfigDict
from shared.utils import load_root_env, ConfigurationError

class ServiceConfig(BaseModel):
    """Service configuration for Selfie AI Analyzer"""
    model_config = ConfigDict(
        extra="ignore",
        case_sensitive=False,
        allow_population_by_field_name=True,
    )
    
    # Service identification
    service_name: str = "selfie-ai-analyzer"
    service_version: str = "1.0.0"
    service_description: str = "ML service for selfie color analysis"
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Environment
    environment: str = Field(..., alias="APP_ENV")
    api_external_port: int = Field(default=8127, alias="SELFIE_ANALYZER_API_EXTERNAL_PORT")
    
    # Security (internal service)
    internal_api_key: str = Field(..., alias="SELFIE_ANALYZER_API_KEY")
    hmac_secret: str | None = Field(None, alias="ANALYZER_HMAC_SECRET")
    hmac_time_skew_seconds: int = 60
    
    # Processing timeouts
    total_analysis_timeout_seconds: int = 24
    deepface_timeout_seconds: int = 5
    mediapipe_timeout_seconds: int = 5
    
    # Queue management
    worker_queue_size: int = 20
    
    # ML configuration
    deepface_thread_lock: bool = True
    deepface_backend: str = "opencv"
    max_face_width_pixels: int = 300
    
    # API configuration
    api_host: str = "0.0.0.0"
    max_image_size_mb: float = 1.5
    
    # Temp file management
    temp_dir: str = "/tmp/selfies"
    temp_cleanup_hours: int = 1
    
    @property
    def api_port(self) -> int:
        """Port based on environment"""
        in_container = os.path.exists("/.dockerenv")
        return 8027 if in_container else self.api_external_port
    
    @property
    def max_image_size_bytes(self) -> int:
        """Max image size in bytes"""
        return int(self.max_image_size_mb * 1024 * 1024)

@lru_cache
def get_service_config() -> ServiceConfig:
    """Load configuration once"""
    try:
        load_root_env()
        return ServiceConfig(**os.environ)
    except Exception as e:
        raise ConfigurationError(
            f"Failed to load config: {e}",
            config_key="selfie-ai-analyzer"
        )