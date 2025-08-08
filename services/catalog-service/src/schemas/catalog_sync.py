from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Literal

# ---------- INPUT DTOs ----------
class SyncRequestIn(BaseModel):
    """Input DTO for starting sync"""
    type: Literal["full"] = Field(..., description="Sync type (only 'full' supported)")
    
    model_config = ConfigDict(extra="forbid")

# ---------- OUTPUT DTOs ----------
class SyncAllowedOut(BaseModel):
    """Response for sync allowed check"""
    allowed: bool
    reason: Literal["ok", "settings_missing", "not_entitled", "sync_active"]
    
    model_config = ConfigDict(from_attributes=True)

class SyncCreatedOut(BaseModel):
    """Response for successful sync creation"""
    syncId: str
    
    model_config = ConfigDict(from_attributes=True)

class SyncStatusOut(BaseModel):
    """Current sync status response"""
    sync: Literal["queued", "running", "synced", "failed"]
    analysis: Literal["idle", "requested", "analyzing", "analyzed", "failed"]
    totalProducts: int
    processedProducts: int
    progress: int  # percentage 0-100
    lastSyncAt: Optional[datetime]
    hasSyncedBefore: bool
    error: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)

class SyncJobOut(BaseModel):
    """Sync job details"""
    syncId: str
    status: str
    startedAt: datetime
    finishedAt: Optional[datetime]
    counts: dict
    
    model_config = ConfigDict(from_attributes=True)

# ---------- Event Payloads ----------
class SyncRequestedPayload(BaseModel):
    """Payload for sync requested event"""
    syncId: str
    shopDomain: str
    type: str

class AnalysisRequestedPayload(BaseModel):
    """Payload for analysis requested event"""
    syncId: str
    shopDomain: str
    productId: str
    variantId: str
    imageUrl: str
    metadata: Optional[dict] = None

class SyncStartedPayload(BaseModel):
    """Payload for sync started event"""
    shopDomain: str
    syncId: str
    totalProducts: int = 0

class SyncProgressPayload(BaseModel):
    """Payload for sync progress event"""
    shopDomain: str
    syncId: str
    submitted: int
    completed: int
    failed: int

class SyncCompletedPayload(BaseModel):
    """Payload for sync completed event"""
    shopDomain: str
    syncId: str
    submitted: int
    completed: int
    failed: int
    durationMs: int

# ================================================================
