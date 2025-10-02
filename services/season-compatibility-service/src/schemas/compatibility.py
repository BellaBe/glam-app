# services/season-compatibility/src/schemas/compatibility.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SeasonScores(BaseModel):
    """All 16 season scores"""

    light_spring: float = Field(ge=0.0, le=1.0)
    true_spring: float = Field(ge=0.0, le=1.0)
    bright_spring: float = Field(ge=0.0, le=1.0)
    warm_spring: float = Field(ge=0.0, le=1.0)
    light_summer: float = Field(ge=0.0, le=1.0)
    true_summer: float = Field(ge=0.0, le=1.0)
    soft_summer: float = Field(ge=0.0, le=1.0)
    cool_summer: float = Field(ge=0.0, le=1.0)
    soft_autumn: float = Field(ge=0.0, le=1.0)
    true_autumn: float = Field(ge=0.0, le=1.0)
    warm_autumn: float = Field(ge=0.0, le=1.0)
    deep_autumn: float = Field(ge=0.0, le=1.0)
    bright_winter: float = Field(ge=0.0, le=1.0)
    true_winter: float = Field(ge=0.0, le=1.0)
    cool_winter: float = Field(ge=0.0, le=1.0)
    deep_winter: float = Field(ge=0.0, le=1.0)


class SeasonCompatibilityOut(SeasonScores):
    """Output DTO for season compatibility"""

    id: UUID
    item_id: str
    merchant_id: str
    product_id: str
    variant_id: str
    primary_season: str
    secondary_season: str
    tertiary_season: str
    max_score: float
    computed_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompatibleItem(BaseModel):
    """Compatible item for API response"""

    item_id: str
    product_id: str
    variant_id: str
    score: float
    matching_season: str


class CompatibleItemsResponse(BaseModel):
    """Response for compatible items query"""

    items: list[CompatibleItem]
    total: int


class SeasonListResponse(BaseModel):
    """Response for available seasons"""

    seasons: list[str]
    total: int = 16
