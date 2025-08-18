# services/catalog-service/src/schemas/events.py
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


# Consumed event payloads
class ProductsFetchedPayload(BaseModel):
    """Payload for platform.products.fetched event"""

    merchant_id: str
    sync_id: str
    platform_name: str
    platform_id: str
    platform_domain: str
    products: list[dict[str, Any]]
    batch_num: int
    has_more: bool


class AnalysisCompletedPayload(BaseModel):
    """Payload for analysis.completed event"""

    merchant_id: str
    item_id: str
    model_version: str
    category: str | None
    subcategory: str | None
    description: str | None
    gender: str | None
    attributes: dict[str, Any] | None
    quality_score: Decimal | None
    confidence_score: Decimal | None
    processing_time_ms: int | None
