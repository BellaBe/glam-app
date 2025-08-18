# services/catalog-analysis/src/config.py
from functools import lru_cache

from pydantic import BaseModel, Field

from shared.utils.config_loader import flatten_config, merged_config


class CatalogAnalysisConfig(BaseModel):
    """Service configuration from YAML + environment"""

    # Service Identity
    service_name: str = Field(..., alias="service.name")
    service_version: str = Field(..., alias="service.version")
    environment: str
    debug: bool

    # Infrastructure
    infrastructure_nats_url: str = Field(..., alias="infrastructure.nats_url")
    infrastructure_redis_url: str = Field(..., alias="infrastructure.redis_url")

    # Logging
    logging_level: str = Field(..., alias="logging.level")
    logging_format: str = Field(..., alias="logging.format")

    # Service-specific configuration
    model_path: str = Field(..., alias="catalog_analysis.model_path")
    products_base_path: str = Field(..., alias="catalog_analysis.products_base_path")
    analysis_dir_name: str = Field(..., alias="catalog_analysis.analysis_dir_name", default="analysis")
    default_colors: int = Field(..., alias="catalog_analysis.default_colors", default=5)
    sample_size: int = Field(..., alias="catalog_analysis.sample_size", default=20000)
    min_chroma: float = Field(..., alias="catalog_analysis.min_chroma", default=8.0)

    @property
    def nats_servers(self) -> list[str]:
        return [self.infrastructure_nats_url]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_service_config() -> CatalogAnalysisConfig:
    """Load and cache service configuration"""
    cfg_dict = merged_config("catalog-analysis", env_prefix="CATALOG_ANALYSIS")
    flattened = flatten_config(cfg_dict)
    return CatalogAnalysisConfig(**flattened)


config = get_service_config()
