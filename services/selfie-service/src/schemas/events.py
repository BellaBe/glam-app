# services/selfie-service/src/schemas/events.py
from datetime import datetime
from typing import Any

from pydantic import BaseModel


# Published events
class AnalysisStartedPayload(BaseModel):
    """Payload for selfie.analysis.started event"""

    analysis_id: str
    merchant_id: str
    platform: dict[str, str]  # {name, shop_id, domain}
    customer_id: str | None = None
    anonymous_id: str | None = None
    image_dimensions: dict[str, int]  # {width, height}
    source: str | None = None
    device_type: str | None = None
    created_at: datetime


class AnalysisCompletedPayload(BaseModel):
    """Payload for selfie.analysis.completed event"""

    analysis_id: str
    merchant_id: str
    platform: dict[str, str]
    customer_id: str | None = None
    anonymous_id: str | None = None
    season_type: str
    confidence: float
    attributes: dict[str, Any] | None = None
    model_version: str | None = None
    processing_time_ms: int | None = None
    completed_at: datetime


class AnalysisFailedPayload(BaseModel):
    """Payload for selfie.analysis.failed event"""

    analysis_id: str
    merchant_id: str
    platform: dict[str, str]
    customer_id: str | None = None
    anonymous_id: str | None = None
    error_code: str
    error_message: str
    failed_at: datetime


class AnalysisClaimedPayload(BaseModel):
    """Payload for selfie.analyses.claimed event"""

    merchant_id: str
    customer_id: str
    anonymous_id: str
    claimed_count: int
    claimed_at: datetime


# Consumed events (from other services)
class RecommendationRequestedPayload(BaseModel):
    """Payload for recommendation.requested event"""

    request_id: str
    merchant_id: str
    customer_id: str
    analysis_id: str
    product_ids: list[str]
    requested_at: datetime
