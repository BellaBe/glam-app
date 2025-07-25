# services/catalog-service/src/events/outbound.py

"""
Events that the CATALOG SERVICE publishes (to other services)
"""

from shared.events.payloads.catalog import (
    SyncRequestedPayload,
    ProductsStoredPayload, 
    SyncCompletedPayload
)


class CatalogOutboundEvents:
    """Events the catalog service publishes"""
    
    # Sync lifecycle events
    SYNC_STARTED = "catalog.sync_started.v1"
    PRODUCTS_STORED = "catalog.products_stored.v1"
    SYNC_COMPLETED = "catalog.sync_completed.v1"
    SYNC_FAILED = "catalog.sync_failed.v1"
    
    # Product events
    PRODUCT_CREATED = "catalog.product_created.v1"
    PRODUCT_UPDATED = "catalog.product_updated.v1"
    PRODUCT_DELETED = "catalog.product_deleted.v1"
    
    # Analysis events
    ANALYSIS_REQUESTED = "analysis.requested.v1"  # Trigger AI analysis
    
    PAYLOAD_SCHEMAS: Dict[str, Type[BaseModel]] = {
        PRODUCTS_STORED: ProductsStoredPayload,
        SYNC_COMPLETED: SyncCompletedPayload,
    }
