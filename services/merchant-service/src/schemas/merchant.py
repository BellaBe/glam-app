from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models.enums import MerchantStatusEnum

# ------------------------------------------------------------------ IN DTOs

class MerchantIn(BaseModel):
    shop_id: str
    shop_domain: str
    shop_name: str
    shop_url: str | None = None
    email: str
    phone: str | None = None
    timezone: str = "UTC"
    country: str | None = None
    currency: str = "USD"
    language: str = "en"
    shopify_access_token: str

    model_config = ConfigDict(extra="forbid")


class MerchantPatch(BaseModel):
    shop_name: str | None = None
    phone: str | None = None
    onboarding_completed: bool | None = None
    onboarding_step: str | None = None

    model_config = ConfigDict(extra="forbid")

# ------------------------------------------------------------------ OUT DTOs

class MerchantStatusOut(BaseModel):
    status: MerchantStatusEnum
    previous_status: MerchantStatusEnum | None
    status_reason: str | None
    changed_at: datetime
    activated_at: datetime | None
    suspended_at: datetime | None
    deactivated_at: datetime | None
    last_activity_at: datetime | None


class MerchantConfigOut(BaseModel):
    # Same fields as original MerchantConfigResponse
    terms_accepted: bool
    terms_accepted_at: datetime | None
    privacy_accepted: bool
    privacy_accepted_at: datetime | None
    widget_enabled: bool
    widget_position: str
    widget_theme: str
    widget_configuration: Dict[str, Any]
    is_marketable: bool
    custom_branding: Dict[str, Any]


class MerchantOut(BaseModel):
    id: UUID
    shop_id: str
    shop_domain: str
    shop_name: str
    shop_url: str | None
    email: str
    phone: str | None
    timezone: str
    country: str | None
    currency: str
    language: str
    platform: str
    onboarding_completed: bool
    onboarding_step: str | None
    created_at: datetime
    updated_at: datetime
    status: MerchantStatusOut | None
    configuration: MerchantConfigOut | None

    model_config = ConfigDict(from_attributes=True)