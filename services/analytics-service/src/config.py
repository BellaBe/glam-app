import os
from functools import lru_cache
from pydantic import BaseModel, Field, SecretStr
from shared.config.loader import merged_config, flatten_config
from shared.database import create_database_config

class AnalyticsConfig(BaseModel):
    """Analytics service configuration from YAML + environment"""
    # Service Identity
    service_name: str = Field(..., alias="service.name")
    service_version: str = Field(..., alias="service.version")
    environment: str
    debug: bool
    
    # API Configuration
    api_host: str = Field(..., alias="api.host")
    api_port: int = Field(..., alias="api.port")
    api_external_port: int = Field(..., alias="api.external_port")
    api_cors_origins: list = Field(..., alias="api.cors_origins")
    
    # Infrastructure
    infrastructure_nats_url: str = Field(..., alias="infrastructure.nats_url")
    infrastructure_redis_url: str = Field(..., alias="infrastructure.redis_url")
    
    # Database Configuration
    db_enabled: bool = Field(..., alias="database.enabled")
    timescale_enabled: bool = Field(True, alias="analytics.timescale_enabled")
    
    # Logging
    logging_level: str = Field(..., alias="logging.level")
    logging_format: str = Field(..., alias="logging.format")
    
    # Analytics-specific features
    batch_size: int = Field(1000, alias="analytics.batch_size")
    processing_interval_seconds: int = Field(30, alias="analytics.processing_interval_seconds")
    calculation_schedule: str = Field("30 2 * * *", alias="analytics.calculation_schedule")
    model_update_schedule: str = Field("0 3 * * 0", alias="analytics.model_update_schedule")
    
    # ML and Prediction Settings
    churn_risk_threshold: float = Field(0.7, alias="analytics.churn_risk_threshold")
    credit_warning_days: int = Field(5, alias="analytics.credit_warning_days")
    anomaly_detection_sensitivity: float = Field(0.95, alias="analytics.anomaly_detection_sensitivity")
    prediction_confidence_level: float = Field(0.90, alias="analytics.prediction_confidence_level")
    model_retrain_days: int = Field(7, alias="analytics.model_retrain_days")
    
    # Alert Configuration
    alert_cooldown_minutes: int = Field(60, alias="analytics.alert_cooldown_minutes")
    alert_max_per_day: int = Field(10, alias="analytics.alert_max_per_day")
    alert_batch_size: int = Field(100, alias="analytics.alert_batch_size")
    notification_timeout_seconds: int = Field(30, alias="analytics.notification_timeout_seconds")
    
    # Data Retention
    raw_data_retention_days: int = Field(90, alias="analytics.raw_data_retention_days")
    aggregated_data_retention_years: int = Field(5, alias="analytics.aggregated_data_retention_years")
    alert_history_retention_days: int = Field(365, alias="analytics.alert_history_retention_days")
    prediction_history_retention_days: int = Field(180, alias="analytics.prediction_history_retention_days")
    
    @property
    def database_config(self):
        """Get database configuration with service prefix"""
        return create_database_config("ANALYTICS_")
    
    @property
    def effective_port(self) -> int:
        """Get effective port based on environment"""
        in_container = any([
            os.getenv("DOCKER_CONTAINER"),
            os.getenv("HOSTNAME", "").startswith("analytics"),
            os.path.exists("/.dockerenv")
        ])
        return self.api_port if in_container else self.api_external_port
    
    @property
    def nats_servers(self) -> list[str]:
        return [self.infrastructure_nats_url]
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

@lru_cache
def get_analytics_config() -> AnalyticsConfig:
    """Load and cache analytics configuration"""
    cfg_dict = merged_config("analytics-service", env_prefix="ANALYTICS")
    flattened = flatten_config(cfg_dict)
    return AnalyticsConfig(**flattened)

# Global config instance
config = get_analytics_config()


