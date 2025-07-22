# ================================================================================================
# services/catalog-analysis/src/dependencies.py
# ================================================================================================
from typing import Annotated
from fastapi import Depends
from shared.messaging.jetstream_wrapper import JetStreamWrapper
from .lifecycle import ServiceLifecycle
from .services.catalog_analysis_service import CatalogAnalysisService
from .events.publishers import CatalogAnalysisEventPublisher

# This file is kept for potential future API needs, but not used in event-driven mode

def get_catalog_analysis_service(lifecycle: ServiceLifecycle) -> CatalogAnalysisService:
    """Get catalog analysis service"""
    if not lifecycle.catalog_analysis_service:
        raise RuntimeError("CatalogAnalysisService not initialized")
    return lifecycle.catalog_analysis_service

def get_publisher(lifecycle: ServiceLifecycle) -> CatalogAnalysisEventPublisher:
    """Get event publisher"""
    if not lifecycle.event_publisher:
        raise RuntimeError("EventPublisher not initialized")
    return lifecycle.event_publisher

# Type aliases
CatalogAnalysisServiceDep = Annotated[CatalogAnalysisService, Depends(get_catalog_analysis_service)]
PublisherDep = Annotated[CatalogAnalysisEventPublisher, Depends(get_publisher)]