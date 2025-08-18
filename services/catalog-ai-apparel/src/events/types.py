# services/catalog-analysis/src/events/types.py
class CatalogAnalysisEvents:
    """Event type constants for catalog item analysis"""

    ITEM_ANALYSIS_REQUESTED = "evt.catalog.item.analysis.requested"
    ITEM_ANALYSIS_COMPLETED = "evt.catalog.item.analysis.completed"
    ITEM_ANALYSIS_FAILED = "evt.catalog.item.analysis.failed"
