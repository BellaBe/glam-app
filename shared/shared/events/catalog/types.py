from pydantic import BaseModel, Field
from typing import Dict, Optional, List, Any

from uuid import UUID


from ..base import EventWrapper

class CatalogCommands:
    """Catalog command types"""
    CATALOG_SYNC_INITIAL = "cmd.catalog.sync_initial"
    CATALOG_SYNC_UPDATE = "cmd.catalog.sync_update"
    CATALOG_PROCESS_IMAGES = "cmd.catalog.process_images"
    CATALOG_ANALYZE_ITEMS = "cmd.catalog.analyze_items"
    CATALOG_ENRICH_WITH_AI = "cmd.catalog.enrich_with_ai"
    
class CatalogEvents:
    """Catalog event types"""
    CATALOG_SYNC_STARTED = "evt.catalog.sync_started"
    CATALOG_SYNC_COMPLETED = "evt.catalog.sync_completed"
    CATALOG_SYNC_FAILED = "evt.catalog.sync_failed"
    CATALOG_IMAGES_PROCESSED = "evt.catalog.images_processed"
    CATALOG_ITEMS_ANALYZED = "evt.catalog.items_analyzed"
    CATALOG_AI_ENRICHED = "evt.catalog.ai_enriched"
    
class CatalogSyncInitialPayload(BaseModel):
    """Payload for initial catalog sync command"""
    merchant_id: UUID
    source: str  # e.g. "shopify", "woocommerce"
    sync_type: str  # e.g. "full", "incremental"
    webhook_url: Optional[str] = None  # Optional webhook for updates
    
class CatalogSyncUpdatePayload(BaseModel):
    """Payload for catalog sync update command"""
    merchant_id: UUID
    items: List[Dict[str, Any]]  # List of items to update
    job_id: Optional[str] = None  # Optional job ID for tracking
    
class CatalogProcessImagesPayload(BaseModel):
    """Payload for processing catalog images"""
    merchant_id: UUID
    items: List[Dict[str, Any]]  # List of items with images to process
    job_id: Optional[str] = None  # Optional job ID for tracking
    
class CatalogAnalyzeItemsPayload(BaseModel):
    """Payload for analyzing catalog items"""
    merchant_id: UUID
    items: List[Dict[str, Any]]  # List of items to analyze
    job_id: Optional[str] = None  # Optional job ID for tracking
    
class CatalogEnrichWithAIPayload(BaseModel):
    """Payload for enriching catalog with AI"""
    merchant_id: UUID
    items: List[Dict[str, Any]]  # List of items to enrich
    job_id: Optional[str] = None  # Optional job ID for tracking
    
class CatalogSyncInitialCommand(EventWrapper):
    """Command to initiate initial catalog sync"""
    subject: str = CatalogCommands.CATALOG_SYNC_INITIAL
    data: CatalogSyncInitialPayload
    
class CatalogSyncUpdateCommand(EventWrapper):
    """Command to update catalog with new items"""
    subject: str = CatalogCommands.CATALOG_SYNC_UPDATE
    data: CatalogSyncUpdatePayload
    
class CatalogProcessImagesCommand(EventWrapper):
    """Command to process catalog images"""
    subject: str = CatalogCommands.CATALOG_PROCESS_IMAGES
    data: CatalogProcessImagesPayload
    
class CatalogAnalyzeItemsCommand(EventWrapper):
    """Command to analyze catalog items"""
    subject: str = CatalogCommands.CATALOG_ANALYZE_ITEMS
    data: CatalogAnalyzeItemsPayload
    
class CatalogEnrichWithAICommand(EventWrapper):
    """Command to enrich catalog with AI"""
    subject: str = CatalogCommands.CATALOG_ENRICH_WITH_AI
    data: CatalogEnrichWithAIPayload
    
class CatalogSyncStartedEvent(EventWrapper):
    """Event emitted when catalog sync starts"""
    subject: str = CatalogEvents.CATALOG_SYNC_STARTED
    data: Dict[str, Any] = Field(default_factory=dict)  # Additional metadata if needed
    
class CatalogSyncCompletedEvent(EventWrapper):
    """Event emitted when catalog sync completes"""
    subject: str = CatalogEvents.CATALOG_SYNC_COMPLETED
    data: Dict[str, Any] = Field(default_factory=dict)  # Additional metadata if needed
    
class CatalogSyncFailedEvent(EventWrapper):
    """Event emitted when catalog sync fails"""
    subject: str = CatalogEvents.CATALOG_SYNC_FAILED
    data: Dict[str, Any] = Field(default_factory=dict)  # Additional metadata if needed
    error_message: Optional[str] = None  # Optional error message for failure
    
class CatalogImagesProcessedEvent(EventWrapper):
    """Event emitted when catalog images are processed"""
    subject: str = CatalogEvents.CATALOG_IMAGES_PROCESSED
    data: Dict[str, Any] = Field(default_factory=dict)  # Additional metadata if needed
    
class CatalogItemsAnalyzedEvent(EventWrapper):
    """Event emitted when catalog items are analyzed"""
    subject: str = CatalogEvents.CATALOG_ITEMS_ANALYZED
    data: Dict[str, Any] = Field(default_factory=dict)  # Additional metadata if needed
    
class CatalogAIEnrichedEvent(EventWrapper):
    """Event emitted when catalog items are enriched with AI"""
    subject: str = CatalogEvents.CATALOG_AI_ENRICHED
    data: Dict[str, Any] = Field(default_factory=dict)  # Additional metadata if needed
    enrichment_details: Optional[Dict[str, Any]] = None  # Optional details about the enrichment process
    
    