# services/catalog-service/src/schemas/events.py
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel

# Consumed event payloads
class ProductsFetchedPayload(BaseModel):
    """Payload for platform.products.fetched event"""
    merchant_id: str
    sync_id: str
    platform_name: str
    platform_shop_id: str
    shop_domain: str
    products: List[Dict[str, Any]]
    batch_num: int
    has_more: bool

class AnalysisCompletedPayload(BaseModel):
    """Payload for analysis.completed event"""
    merchant_id: str
    item_id: str
    model_version: str
    category: Optional[str]
    subcategory: Optional[str]
    description: Optional[str]
    gender: Optional[str]
    attributes: Optional[Dict[str, Any]]
    quality_score: Optional[Decimal]
    confidence_score: Optional[Decimal]
    processing_time_ms: Optional[int]