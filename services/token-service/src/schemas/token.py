# services/token-service/src/schemas/token.py

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List

# Input DTOs
class StoreTokenRequest(BaseModel):
    """Request to store a token"""
    merchant_id: str = Field(..., description="Internal merchant ID")
    platform_name: str = Field(..., description="Platform name (shopify, woocommerce, etc)")
    platform_shop_id: str = Field(..., description="Shop ID in the platform")
    shop_domain: str = Field(..., description="Full domain")
    token_data: Dict[str, Any] = Field(..., description="Token data to encrypt")
    token_type: str = Field(..., description="Token type (oauth, api_key, etc)")
    expires_at: Optional[datetime] = Field(None, description="Token expiration")
    scopes: Optional[str] = Field(None, description="OAuth scopes")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "merchant_id": "uuid-merchant-id",
                "platform_name": "shopify",
                "platform_shop_id": "12345678",
                "shop_domain": "example.myshopify.com",
                "token_data": {
                    "access_token": "shpat_xxx",
                    "scope": "read_products,write_orders"
                },
                "token_type": "oauth",
                "expires_at": "2024-12-31T23:59:59Z",
                "scopes": "read_products,write_orders"
            }
        }
    )

# Output DTOs
class TokenData(BaseModel):
    """Decrypted token data"""
    platform_name: str
    platform_shop_id: str
    shop_domain: str
    token_data: Dict[str, Any]
    token_type: str
    expires_at: Optional[datetime]
    is_expired: bool
    scopes: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)

class TokenListResponse(BaseModel):
    """Response with list of tokens"""
    tokens: List[TokenData]

class StoreTokenResponse(BaseModel):
    """Response after storing token"""
    token_id: str
    status: str

class DeleteTokenResponse(BaseModel):
    """Response after deleting token"""
    status: str