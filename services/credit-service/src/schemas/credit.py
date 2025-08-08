from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

# ---------- INPUT DTOs ----------
class CreditGrantIn(BaseModel):
    """Input DTO for granting credits"""
    shop_domain: str = Field(..., alias="shopDomain")
    amount: int = Field(..., gt=0)
    reason: str = Field(..., pattern="^(trial|subscription|manual|one_time_pack)$")
    external_ref: Optional[str] = Field(None, alias="externalRef")
    metadata: Optional[dict] = None
    
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    
    @field_validator('shop_domain')
    def validate_shop_domain(cls, v: str) -> str:
        v = v.lower().strip()
        if not v.endswith('.myshopify.com'):
            raise ValueError("Shop domain must end with .myshopify.com")
        return v

# ---------- OUTPUT DTOs ----------
class BalanceOut(BaseModel):
    """Output DTO for balance query"""
    balance: int
    updated_at: datetime = Field(..., alias="updatedAt")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class CreditGrantOut(BaseModel):
    """Output DTO for grant result"""
    ok: bool
    balance: int
    idempotent: bool = False
    
    model_config = ConfigDict(from_attributes=True)

class LedgerEntryOut(BaseModel):
    """Output DTO for ledger entry"""
    id: str
    amount: int
    reason: str
    external_ref: Optional[str] = Field(None, alias="externalRef")
    metadata: Optional[dict] = None
    created_at: datetime = Field(..., alias="createdAt")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class LedgerOut(BaseModel):
    """Output DTO for ledger query"""
    entries: List[LedgerEntryOut]
    total: int
    
    model_config = ConfigDict(from_attributes=True)

# ---------- EVENT PAYLOADS ----------
class CreditGrantEvent(BaseModel):
    """Event payload for credit grant"""
    shop_domain: str = Field(..., alias="shopDomain")
    credits: int
    reason: str
    external_ref: Optional[str] = Field(None, alias="externalRef")
    metadata: Optional[dict] = None
    correlation_id: str
    
    model_config = ConfigDict(populate_by_name=True)

class TrialActivatedEvent(BaseModel):
    """Event payload for trial activation"""
    shop_domain: str = Field(..., alias="shopDomain")
    ends_at: datetime = Field(..., alias="endsAt")
    days: int
    trial_credits: Optional[int] = Field(None, alias="trialCredits")
    correlation_id: str
    
    model_config = ConfigDict(populate_by_name=True)

class BalanceChangedEvent(BaseModel):
    """Event payload for balance change"""
    shop_domain: str = Field(..., alias="shopDomain")
    delta: int
    new_balance: int = Field(..., alias="newBalance")
    reason: str
    external_ref: Optional[str] = Field(None, alias="externalRef")
    at: datetime
    
    model_config = ConfigDict(populate_by_name=True)

class BalanceLowEvent(BaseModel):
    """Event payload for low balance"""
    shop_domain: str = Field(..., alias="shopDomain")
    balance: int
    threshold: int
    at: datetime
    
    model_config = ConfigDict(populate_by_name=True)

class BalanceDepletedEvent(BaseModel):
    """Event payload for depleted balance"""
    shop_domain: str = Field(..., alias="shopDomain")
    at: datetime
    
    model_config = ConfigDict(populate_by_name=True)

