# services/catalog-ai-analyzer/src/schemas/events.py
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel
from .analysis import AnalysisItem, AnalysisConfig, ItemAnalysisResult

# Input Events
class CatalogAnalysisRequestedPayload(BaseModel):
    """evt.catalog.ai.analysis.requested payload"""
    merchant_id: UUID
    sync_id: UUID
    correlation_id: str
    items: List[AnalysisItem]
    analysis_config: Optional[AnalysisConfig] = None

# Output Events
class CatalogAnalysisCompletedPayload(ItemAnalysisResult):
    """evt.catalog.ai.analysis.completed payload"""
    pass

class CatalogBatchCompletedPayload(BaseModel):
    """evt.catalog.ai.batch.completed payload"""
    merchant_id: UUID
    sync_id: UUID
    correlation_id: str
    processed: int
    failed: int
    partial: int
    total_time_ms: int