# services/catalog-ai-analyzer/src/schemas/analysis.py
from uuid import UUID
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# Analysis DTOs
class AnalysisItem(BaseModel):
    """Single item for analysis"""
    item_id: UUID
    product_id: str  # Platform product ID (e.g., "8526062977266")
    variant_id: str  # Platform variant ID (e.g., "46547096469746")
    image_url: str
    metadata: Optional[Dict[str, Any]] = None

class AnalysisConfig(BaseModel):
    """Analysis configuration"""
    enable_color: bool = True
    enable_attributes: bool = True
    max_colors: int = 5

class ColorResult(BaseModel):
    """Color analysis result"""
    name: str
    confidence: float
    hex: str

class PatternResult(BaseModel):
    """Pattern analysis result"""
    name: str
    confidence: float

class AttributeResult(BaseModel):
    """AI-extracted attributes"""
    colors: List[ColorResult] = []
    patterns: List[PatternResult] = []
    styles: List[Dict[str, Any]] = []
    materials: List[Dict[str, Any]] = []
    season: List[str] = []
    occasion: List[str] = []

class PreciseColors(BaseModel):
    """MediaPipe precise color extraction"""
    rgb_values: List[List[int]]
    color_count: int
    extraction_method: str = "mediapipe_lab_kmeans"

class AnalysisMetadata(BaseModel):
    """Analysis metadata"""
    analyzers_used: List[str]
    quality_score: float
    confidence_score: float
    processing_times: Dict[str, int]

class ItemAnalysisResult(BaseModel):
    """Complete analysis result for a single item"""
    merchant_id: UUID
    item_id: UUID
    product_id: str
    variant_id: str
    correlation_id: str
    service_version: str = "v1.0.0"
    status: str  # success|partial|failed
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    gender: Optional[str] = None
    attributes: Optional[AttributeResult] = None
    precise_colors: Optional[PreciseColors] = None
    analysis_metadata: AnalysisMetadata
    error: Optional[str] = None