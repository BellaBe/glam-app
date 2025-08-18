# services/catalog-analysis/src/schemas/catalog_item.py

from pydantic import BaseModel, Field


class CatalogItemAnalysisRequest(BaseModel):
    """Input DTO for catalog item analysis request"""

    shop_id: str = Field(..., example="70931710194")
    product_id: str = Field(..., example="8526062977266")
    variant_id: str = Field(..., example="46547096469746")


class CatalogItemAnalysisResult(BaseModel):
    """Output DTO for catalog item analysis result - maintains original API format"""

    status: str
    colours: list[list[int]] | None = None
    latency_ms: int
    error: str | None = None
    shop_id: str
    product_id: str
    variant_id: str
