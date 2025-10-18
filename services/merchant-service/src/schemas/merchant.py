# services/merchant-service/src/schemas/merchant.py
from __future__ import annotations
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

MerchantStatus = Literal["PENDING", "ACTIVE", "PAUSED", "SUSPENDED", "UNINSTALLED"]


class MerchantSyncIn(BaseModel):
    """Input schema for syncing merchant from platform"""
    platform_shop_id: str = Field(..., description="Platform shop ID")
    domain: str = Field(..., description="Merchant domain")
    name: str = Field(..., description="Merchant name")
    email: str = Field(..., description="Merchant email")
    primary_domain: str | None = Field(None, description="Primary domain")
    currency: str = Field(..., description="Currency code")
    country: str = Field(..., description="Country code")
    platform_version: str | None = Field(None, description="Platform version")
    scopes: str = Field(..., description="OAuth scopes")

    @field_validator("domain", "primary_domain")
    @classmethod
    def validate_domain(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not v or len(v) < 3 or "." not in v:
            raise ValueError("Invalid domain format")
        return v.lower()


class MerchantOut(BaseModel):
    """Output schema for merchant"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    platform_name: str
    platform_shop_id: str
    domain: str
    name: str
    email: str
    primary_domain: str | None
    currency: str
    country: str
    platform_version: str | None
    scopes: str
    status: MerchantStatus
    installed_at: datetime | None
    uninstalled_at: datetime | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime


class MerchantSyncResponse(BaseModel):
    """Response schema for merchant sync"""
    created: bool
    merchant_id: UUID
