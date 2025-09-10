# merchant/api/schemas.py
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

MerchantStatus = Literal["PENDING", "ACTIVE", "PAUSED", "SUSPENDED", "UNINSTALLED"]


class MerchantSyncIn(BaseModel):
    """
    Body for /sync (Shopify BFF -> merchant-service).
    NOTE: platform_name and domain come from headers via RequestContext.
    """

    platform_shop_id: str = Field(..., description="Platform shop ID (e.g., Shopify GID)")
    shop_name: str = Field(..., description="Display name of the shop")
    email: EmailStr
    primary_domain: str | None = None
    currency: str = Field(..., min_length=3, max_length=3, description="ISO 4217 code")
    country: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2")
    platform_version: str | None = None
    scopes: str


class MerchantSyncOut(BaseModel):
    """Minimal result for after-auth hook—client doesn't consume events."""

    success: bool


class MerchantOut(BaseModel):
    """Snapshot for dashboard (/self)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    platform_name: str
    platform_shop_id: str
    domain: str

    name: str
    email: EmailStr
    primary_domain: str | None
    currency: str
    country: str
    platform_version: str | None
    scopes: str

    installed_at: datetime | None
    uninstalled_at: datetime | None

    status: MerchantStatus
    last_synced_at: datetime | None  # <- aligns with DB

    created_at: datetime
    updated_at: datetime
