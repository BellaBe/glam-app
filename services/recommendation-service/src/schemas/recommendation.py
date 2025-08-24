# services/recommendation-service/src/schemas/recommendation.py
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, Dict, List


class RecommendationRequest(BaseModel):
    """Request for creating recommendations"""
    analysis_id: str = Field(..., description="Reference to AI analysis")
    shopper_id: Optional[str] = Field(None, description="External shopper ID")
    anonymous_id: Optional[str] = Field(None, description="Anonymous session ID")
    primary_season: str = Field(..., description="Main season type")
    secondary_season: Optional[str] = Field(None, description="Secondary preference")
    tertiary_season: Optional[str] = Field(None, description="Tertiary preference")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    season_scores: Dict[str, float] = Field(..., description="All 16 season scores")
    
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
    matches: List[MatchItemOut]
    
    model_config = ConfigDict(from_attributes=True)


class MatchOut(BaseModel):
    """Complete match record output"""
    id: UUID
    merchant_id: UUID
    platform_name: str
    platform_domain: str
    analysis_id: str
    shopper_id: Optional[str]
    anonymous_id: Optional[str]
    primary_season: str
    secondary_season: Optional[str]
    tertiary_season: Optional[str]
    confidence: float
    season_scores: Dict[str, float]
    total_matches: int
    top_score: Optional[float]
    created_at: datetime
    match_items: List[MatchItemOut] = []
    
    model_config = ConfigDict(from_attributes=True)