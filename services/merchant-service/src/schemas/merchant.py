from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, EmailStr, field_validator
from typing import Optional, Dict, Any
from prisma.enums import MerchantStatus, ConsentType

# ---------- INPUT DTOs ----------
class MerchantSync(BaseModel):
    """Input DTO for syncing merchant"""
    platform_name: str = Field(..., description="Platform name (e.g., Shopify)")
    platform_id: str = Field(..., description="Shopify Global ID (e.g., gid://shopify/Shop/123)")
    shop_name: str = Field(..., description="Shop display name")
    shop_url: str = Field(None, description="Shop URL")
    email: EmailStr = Field(None, description="Primary contact email")
    contact_email: EmailStr = Field(None, description="Contact email for support")
    currency_code: str = Field("USD", description="ISO currency code")
    primary_domain_url: str = Field(None, description="Primary domain (e.g., example.com)")
    primary_domain_host: str = Field(None, description="Primary domain host (e.g., example.com)")
    myshopify_domain: str = Field(None, description="MyShopify domain (e.g., example.myshopify.com)")
    platform_plan: str = Field(None, description="Shop plan name")
    billing_address: str = Field(None, description="Billing address in JSON format")
    
    model_config = ConfigDict(extra="forbid")


class MerchantSettingsUpdate(BaseModel):
    """Input DTO for updating merchant settings"""
    data_access: Optional[bool] = None
    auto_sync: Optional[bool] = None
    tos: Optional[bool] = None
    
    model_config = ConfigDict(extra="forbid")

class MerchantActivity(BaseModel):
    """Input DTO for recording merchant activity"""
    activity_type: str = Field(..., description="Type of activity (e.g., page_view, feature_use)")
    activity_name: str = Field(..., description="Specific activity name")
    activity_data: Optional[Dict[str, Any]] = Field(None, description="Additional activity data")
    
    model_config = ConfigDict(extra="forbid")

# ---------- OUTPUT DTOs ----------
class MerchantOut(BaseModel):
    """Output DTO for merchant"""
    merchant_id: str
    shop_domain: str
    shop_gid: str
    shop_name: Optional[str]
    email: Optional[str]
    timezone: str
    currency: str
    installed_at: datetime
    uninstalled_at: Optional[datetime]
    last_auth_at: Optional[datetime]
    last_activity_at: Optional[datetime]
    status: MerchantStatus
    status_reason: Optional[str]
    settings_accepted: bool = False  # Derived field
    
    model_config = ConfigDict(from_attributes=True)

class MerchantSettingsOut(BaseModel):
    """Output DTO for merchant settings"""
    data_access: bool
    auto_sync: bool
    tos: bool
    
    model_config = ConfigDict(from_attributes=True)

class MerchantSyncOut(BaseModel):
    """Output DTO for merchant sync result"""
    created: bool
    merchant_id: str
    
    model_config = ConfigDict(from_attributes=True)

# ---------- EVENT PAYLOADS ----------
class MerchantCreatedPayload(BaseModel):
    """Payload for evt.merchant.created"""
    merchant_id: str
    shop_gid: str
    shop_domain: str
    shop_name: Optional[str]
    email: Optional[str]
    timezone: str
    currency: str
    platform: str
    installed_at: datetime
    install_source: Optional[str]

class MerchantSyncedPayload(BaseModel):
    """Payload for evt.merchant.synced"""
    merchant_id: str
    shop_gid: str
    shop_domain: str
    first_install: bool
    last_auth_at: datetime
    scopes: str

class MerchantSettingsUpdatedPayload(BaseModel):
    """Payload for evt.merchant.settings.updated"""
    merchant_id: str
    shop_gid: str
    shop_domain: str
    changes: Dict[str, bool]
    updated_at: datetime

class MerchantStatusChangedPayload(BaseModel):
    """Payload for evt.merchant.status.changed"""
    merchant_id: str
    shop_gid: str
    old_status: MerchantStatus
    new_status: MerchantStatus
    reason: str
    changed_at: datetime

class MerchantUninstalledPayload(BaseModel):
    """Payload for evt.merchant.uninstalled"""
    merchant_id: str
    shop_gid: str
    shop_domain: str
    uninstalled_at: datetime
    uninstall_reason: Optional[str]

class MerchantActivityRecordedPayload(BaseModel):
    """Payload for evt.merchant.activity.recorded"""
    merchant_id: str
    shop_gid: str
    activity_type: str
    activity_name: str
    activity_data: Optional[Dict[str, Any]]
    timestamp: datetime

