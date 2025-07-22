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
    
    
# services/merchant-service/src/schemas/merchant.py
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from ..models.enums import MerchantStatusEnum

# ---------- INPUT DTOs ----------
class MerchantBootstrap(BaseModel):
    """Bootstrap DTO for merchant creation from webhook"""
    shop_id: str
    shop_domain: str
    shop_name: str
    shop_url: Optional[str] = None
    email: str
    phone: Optional[str] = None
    timezone: str = "UTC"
    country: Optional[str] = None
    currency: str = "USD"
    language: str = "en"
    shopify_access_token: str
    
    model_config = ConfigDict(extra="forbid")

class InstallationRecordCreate(BaseModel):
    """Create DTO for installation record"""
    platform: str = "shopify"
    install_channel: Optional[str] = None
    installed_by: Optional[str] = None
    installation_ip: Optional[str] = None
    app_version: Optional[str] = None
    platform_api_version: Optional[str] = None
    permissions_granted: List = []
    callbacks_configured: List = []
    referral_code: Optional[str] = None
    utm: Dict = {}
    platform_metadata: Dict = {}
    
    model_config = ConfigDict(extra="forbid")

class MerchantUpdate(BaseModel):
    """Update DTO for merchant"""
    shop_name: Optional[str] = None
    shop_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    language: Optional[str] = None
    
    model_config = ConfigDict(extra="forbid")

class MerchantConfigUpdate(BaseModel):
    """Update DTO for merchant configuration"""
    widget_enabled: Optional[bool] = None
    widget_position: Optional[str] = None
    widget_theme: Optional[str] = None
    widget_configuration: Optional[Dict] = None
    is_marketable: Optional[bool] = None
    custom_css: Optional[str] = None
    custom_branding: Optional[Dict] = None
    
    model_config = ConfigDict(extra="forbid")

class ActivityRecord(BaseModel):
    """Activity record DTO"""
    activity_type: str
    activity_name: str
    activity_description: Optional[str] = None
    activity_data: Dict = {}
    session_id: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    
    model_config = ConfigDict(extra="forbid")

# ---------- OUTPUT DTOs ----------
class MerchantStatusResponse(BaseModel):
    """Output DTO for merchant status"""
    status: MerchantStatusEnum
    previous_status: Optional[MerchantStatusEnum]
    status_reason: Optional[str]
    changed_at: datetime
    activated_at: Optional[datetime]
    suspended_at: Optional[datetime] 
    deactivated_at: Optional[datetime]
    last_activity_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)

class MerchantConfigResponse(BaseModel):
    """Output DTO for merchant configuration"""
    terms_accepted: bool
    terms_accepted_at: Optional[datetime]
    privacy_accepted: bool
    privacy_accepted_at: Optional[datetime]
    widget_enabled: bool
    widget_position: str
    widget_theme: str
    widget_configuration: Optional[Dict[str, Any]]
    is_marketable: bool
    custom_branding: Optional[Dict[str, Any]]
    
    model_config = ConfigDict(from_attributes=True)

class MerchantResponse(BaseModel):
    """Output DTO for merchant"""
    id: UUID
    shop_id: str
    shop_domain: str
    shop_name: str
    shop_url: Optional[str]
    email: str
    phone: Optional[str]
    timezone: str
    country: Optional[str]
    currency: str
    language: str
    platform: str
    onboarding_completed: bool
    onboarding_step: Optional[str]
    created_at: datetime
    updated_at: datetime
    status: MerchantStatusResponse
    configuration: MerchantConfigResponse
    
    model_config = ConfigDict(from_attributes=True)