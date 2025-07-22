# src/events/types.py
class CatalogEvents:
    """Catalog event type constants"""
    # Outgoing events
    SYNC_FETCH_REQUESTED = "sync.fetch.requested.v1"
    ANALYSIS_REQUEST = "analysis.request.v1"
    
    # Incoming events
    SYNC_PRODUCTS_FETCHED = "sync.products.fetched.v1"
    ANALYSIS_COMPLETED = "analysis.completed.v1"
    ANALYSIS_FAILED = "analysis.failed.v1"