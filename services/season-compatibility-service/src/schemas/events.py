# services/season-compatibility/src/schemas/events.py

from pydantic import BaseModel


class PreciseColors(BaseModel):
    """Precise RGB colors from AI analysis"""

    rgb_values: list[list[int]]


class ColorInfo(BaseModel):
    """Color information"""

    name: str
    hex: str


class Attributes(BaseModel):
    """Product attributes from AI analysis"""

    colors: list[ColorInfo] = []
    materials: list[str] = []
    patterns: list[str] = []
    styles: list[str] = []


class AIAnalysisCompletedPayload(BaseModel):
    """Input event from AI Analysis Service"""

    item_id: str
    merchant_id: str
    product_id: str
    variant_id: str
    precise_colors: PreciseColors
    attributes: Attributes
    correlation_id: str | None = None


class TopSeasons(BaseModel):
    """Top 3 seasons"""

    primary: str
    secondary: str
    tertiary: str


class ComputationMetadata(BaseModel):
    """Metadata about the computation"""

    colors_analyzed: int
    attributes_used: list[str]
    computation_time_ms: float
    algorithm_version: str = "v1.0.0"


class SeasonComputationCompletedPayload(BaseModel):
    """Output event for Analytics Service"""

    item_id: str
    merchant_id: str
    product_id: str
    variant_id: str
    correlation_id: str
    season_scores: dict[str, float]
    top_seasons: TopSeasons
    max_score: float
    computation_metadata: ComputationMetadata
