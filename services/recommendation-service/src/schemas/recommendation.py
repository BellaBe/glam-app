# services/recommendation-service/src/schemas/recommendation.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RecommendationRequest(BaseModel):
    """Request for creating recommendations"""

    analysis_id: str = Field(..., description="Reference to AI analysis")
    shopper_id: str | None = Field(None, description="External shopper ID")
    anonymous_id: str | None = Field(None, description="Anonymous session ID")
    primary_season: str = Field(..., description="Main season type")
    secondary_season: str | None = Field(None, description="Secondary preference")
    tertiary_season: str | None = Field(None, description="Tertiary preference")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    season_scores: dict[str, float] = Field(..., description="All 16 season scores")

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_shopper_id(self):
        if not self.shopper_id and not self.anonymous_id:
            raise ValueError("Either shopper_id or anonymous_id is required")
        return self


class MatchItemOut(BaseModel):
    """Output for individual match item"""

    item_id: str
    product_id: str
    variant_id: str
    score: float
    matching_season: str

    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseModel):
    """Response for recommendation request"""

    match_id: str
    total_matches: int
    matches: list[MatchItemOut]

    model_config = ConfigDict(from_attributes=True)


class MatchOut(BaseModel):
    """Complete match record output"""

    id: UUID
    merchant_id: UUID
    platform_name: str
    domain: str
    analysis_id: str
    shopper_id: str | None
    anonymous_id: str | None
    primary_season: str
    secondary_season: str | None
    tertiary_season: str | None
    confidence: float
    season_scores: dict[str, float]
    total_matches: int
    top_score: float | None
    created_at: datetime
    match_items: list[MatchItemOut] = []

    model_config = ConfigDict(from_attributes=True)
