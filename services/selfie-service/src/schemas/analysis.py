# services/selfie-service/src/schemas/analysis.py
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AnalysisStatus(str, Enum):
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Input DTOs
class AnalysisCreate(BaseModel):
    """DTO for creating analysis"""

    id: str
    merchant_id: str
    platform_name: str
    platform_shop_id: str
    platform_domain: str
    customer_id: str | None = None
    anonymous_id: str | None = None
    image_hash: str
    image_width: int
    image_height: int
    blur_score: float | None = None
    exposure_score: float | None = None
    face_area_ratio: float | None = None
    source: str | None = None
    device_type: str | None = None
    status: AnalysisStatus = AnalysisStatus.PROCESSING

    model_config = ConfigDict(extra="forbid")


# Output DTOs
class AnalysisOut(BaseModel):
    """DTO for analysis response"""

    id: str
    merchant_id: str
    platform_name: str
    platform_shop_id: str
    platform_domain: str
    customer_id: str | None = None
    anonymous_id: str | None = None
    status: AnalysisStatus
    progress: int = 0

    # Quality metrics
    blur_score: float | None = None
    exposure_score: float | None = None
    face_area_ratio: float | None = None

    # AI Results
    primary_season: str | None = None
    secondary_season: str | None = None
    confidence: float | None = None
    attributes: dict[str, Any] | None = None
    model_version: str | None = None
    processing_time: int | None = None

    # Error info
    error_code: str | None = None
    error_message: str | None = None

    # Metadata
    source: str | None = None
    device_type: str | None = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    claimed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisStatusResponse(BaseModel):
    """DTO for status endpoint"""

    id: str
    status: str
    progress: int
    message: str


class ClaimRequest(BaseModel):
    """DTO for claim request"""

    customer_id: str = Field(..., description="Customer ID")
    anonymous_id: str = Field(..., description="Anonymous ID to claim")

    model_config = ConfigDict(extra="forbid")


class ClaimResponse(BaseModel):
    """DTO for claim response"""

    claimed: int = Field(..., description="Number of analyses claimed")
