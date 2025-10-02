# services/selfie-ai-analyzer/src/schemas/analysis.py
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List

# Request DTOs
class AnalysisRequest(BaseModel):
    """Request for selfie analysis"""
    analysis_id: str = Field(..., pattern="^ana_[a-zA-Z0-9]+$")
    merchant_id: str = Field(..., pattern="^merch_[a-zA-Z0-9]+$")
    image_jpeg_b64: str = Field(..., description="Base64 encoded JPEG ≤1.5MB")
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    model_config = ConfigDict(extra="forbid")

# Response DTOs
class SeasonScores(BaseModel):
    """Seasonal color analysis scores"""
    light_spring: float = Field(ge=0, le=1)
    true_spring: float = Field(ge=0, le=1)
    bright_spring: float = Field(ge=0, le=1)
    warm_spring: float = Field(ge=0, le=1)
    light_summer: float = Field(ge=0, le=1)
    true_summer: float = Field(ge=0, le=1)
    soft_summer: float = Field(ge=0, le=1)
    cool_summer: float = Field(ge=0, le=1)
    soft_autumn: float = Field(ge=0, le=1)
    true_autumn: float = Field(ge=0, le=1)
    warm_autumn: float = Field(ge=0, le=1)
    deep_autumn: float = Field(ge=0, le=1)
    bright_winter: float = Field(ge=0, le=1)
    true_winter: float = Field(ge=0, le=1)
    cool_winter: float = Field(ge=0, le=1)
    deep_winter: float = Field(ge=0, le=1)

class Demographics(BaseModel):
    """Optional demographics data"""
    age: int = Field(ge=0, le=120)
    gender: str = Field(pattern="^[mfu]$")  # m/f/u
    race: str

class ColorInfo(BaseModel):
    """Color information for a region"""
    dominant_rgb: List[int] = Field(min_length=3, max_length=3)
    colors: List[List[int]]

class ColorAttributes(BaseModel):
    """Color attributes by region"""
    hair: Optional[ColorInfo] = None
    face_skin: Optional[ColorInfo] = None
    left_iris: Optional[ColorInfo] = None
    right_iris: Optional[ColorInfo] = None

class AnalysisMetrics(BaseModel):
    """Analysis metrics"""
    face_landmarks_count: int
    segmentation_classes: int
    colors_extracted: int
    undertone: str
    contrast_level: str

class ModelVersions(BaseModel):
    """Model version info"""
    deepface: str
    mediapipe: str
    algorithm: str

class AnalysisResponse(BaseModel):
    """Successful analysis response"""
    success: bool = True
    analysis_id: str
    season_scores: SeasonScores
    primary_season: str
    secondary_season: str
    tertiary_season: str
    confidence: float = Field(ge=0, le=1)
    demographics: Optional[Demographics] = None
    color_attributes: ColorAttributes
    analysis_metrics: AnalysisMetrics
    warnings: List[str] = Field(default_factory=list)
    model_versions: ModelVersions
    processing_ms: int