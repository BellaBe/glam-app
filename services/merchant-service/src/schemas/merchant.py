# services/merchant-service/src/schemas/merchant.py
from prisma.enums import MerchantStatus
from pydantic import BaseModel, Field


# ---------- INPUT DTOs ----------
class MerchantSyncIn(BaseModel):
    """Input DTO for syncing merchant"""

    platform_name: str = Field(..., description="Platform name (e.g., Shopify)")
    platform_shop_id: str = Field(..., description="Shopify Global ID (e.g., gid://shopify/Shop/123)")
    domain: str = Field(..., description="Shop domain (e.g., myshopify.com)")
    shop_name: str = Field(..., description="Shop display name")
    email: str = Field(..., description="Shop contact email")
    primary_domain_host: str = Field(..., description="Primary domain of the shop")
    currency: str = Field(..., description="Shop currency (e.g., USD)")
    country: str = Field(..., description="Shop country code (e.g., US)")
    platform_version: str = Field(..., description="Shopify API version (e.g., 2025-01)")
    scopes: str = Field(..., description="OAuth scopes granted by the shop")


class MerchantSyncOut(BaseModel):
    """Output DTO for merchant sync result"""

    created: bool = Field(..., description="Indicates if the merchant was newly created")
    merchant_id: str = Field(..., description="Unique identifier of the merchant")


class MerchantSelfOut(BaseModel):
    """Output DTO for self merchant"""

    id: str
    platform_shop_id: str
    domain: str
    shop_name: str
    status: MerchantStatus
