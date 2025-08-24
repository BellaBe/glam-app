# services/selfie-service/src/schemas/events.py
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

# Published events
class AnalysisStartedPayload(BaseModel):
    """Payload for selfie.analysis.started event"""
    analysis_id: str
    merchant_id: str
    platform: Dict[str, str]  # {name, shop_id, domain}
    customer_id: Optional[str] = None
    anonymous_id: Optional[str] = None
    image_dimensions: Dict[str, int]  # {width, height}
    source: Optional[str] = None
    device_type: Optional[str] = None
    created_at: datetime

class AnalysisCompletedPayload(BaseModel):
    """Payload for selfie.analysis.completed event"""
    analysis_id: str
    merchant_id: str
    platform: Dict[str, str]
    customer_id: Optional[str] = None
    anonymous_id: Optional[str] = None
    season_type: str
    confidence: float
    attributes: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = None
    processing_time_ms: Optional[int] = None
    completed_at: datetime

class AnalysisFailedPayload(BaseModel):
    """Payload for selfie.analysis.failed event"""
    analysis_id: str
    merchant_id: str
    platform: Dict[str, str]
    customer_id: Optional[str] = None
    anonymous_id: Optional[str] = None
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