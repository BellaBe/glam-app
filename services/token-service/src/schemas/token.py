# services/token-service/src/schemas/token.py

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# Input DTOs
class StoreTokenRequest(BaseModel):
    """Request to store a token"""

    merchant_id: str = Field(..., description="Internal merchant ID")
    platform_name: str = Field(..., description="Platform name (shopify, woocommerce, etc)")
    platform_shop_id: str = Field(..., description="Shop ID in the platform")
    domain: str = Field(..., description="Full domain")
    token_data: dict[str, Any] = Field(..., description="Token data to encrypt")
    token_type: str = Field(..., description="Token type (oauth, api_key, etc)")
    expires_at: datetime | None = Field(None, description="Token expiration")
    scopes: str | None = Field(None, description="OAuth scopes")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "merchant_id": "uuid-merchant-id",
                "platform_name": "shopify",
                "platform_shop_id": "12345678",
                "domain": "example.myshopify.com",
                "token_data": {"access_token": "shpat_xxx", "scope": "read_products,write_orders"},
                "token_type": "oauth",
                "expires_at": "2024-12-31T23:59:59Z",
                "scopes": "read_products,write_orders",
            }
        }
    )


# Output DTOs
class TokenData(BaseModel):
    """Decrypted token data"""

    platform_name: str
    platform_shop_id: str
    domain: str
    token_data: dict[str, Any]
    token_type: str
    expires_at: datetime | None
    is_expired: bool
    scopes: str | None

    model_config = ConfigDict(from_attributes=True)


class TokenListResponse(BaseModel):
    """Response with list of tokens"""

    tokens: list[TokenData]


class StoreTokenResponse(BaseModel):
    """Response after storing token"""

    token_id: str
    status: str


class DeleteTokenResponse(BaseModel):
    """Response after deleting token"""

    status: str
