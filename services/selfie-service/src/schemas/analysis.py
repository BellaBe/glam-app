# services/selfie-service/src/schemas/analysis.py
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from enum import Enum

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
    customer_id: Optional[str] = None
    anonymous_id: Optional[str] = None
    image_hash: str
    image_width: int
    image_height: int
    blur_score: Optional[float] = None
    exposure_score: Optional[float] = None
    face_area_ratio: Optional[float] = None
    source: Optional[str] = None
    device_type: Optional[str] = None
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
    customer_id: Optional[str] = None
    anonymous_id: Optional[str] = None
    status: AnalysisStatus
    progress: int = 0
    
    # Quality metrics
    blur_score: Optional[float] = None
    exposure_score: Optional[float] = None
    face_area_ratio: Optional[float] = None
    
    # AI Results
    primary_season: Optional[str] = None
    secondary_season: Optional[str] = None
    confidence: Optional[float] = None
    attributes: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = None
    processing_time: Optional[int] = None
    
    # Error info
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    # Metadata
    source: Optional[str] = None
    device_type: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    claimed_at: Optional[datetime] = None
    
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