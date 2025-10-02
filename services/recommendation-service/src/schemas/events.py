# services/recommendation-service/src/schemas/events.py
from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class MatchCompletedPayload(BaseModel):
    """Payload for recommendation.match.completed event"""
    merchant_id: UUID
    match_id: str
    shopper_id: Optional[str]
    anonymous_id: Optional[str]
    matches_count: int
    primary_season: str
    correlation_id: str


class MatchFailedPayload(BaseModel):
    """Payload for recommendation.match.failed event"""
    merchant_id: UUID
    error_code: str
    reason: str
    correlation_id: str
    analysis_id: Optional[str] = None