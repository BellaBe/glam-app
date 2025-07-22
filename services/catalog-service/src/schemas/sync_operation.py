# src/schemas/sync.py
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from ..models.enums import SyncType, SyncOperationStatus

class SyncOperationIn(BaseModel):
    """Input DTO for creating sync operation"""
    shop_id: str = Field(..., min_length=1, max_length=100)
    sync_type: SyncType = SyncType.FULL
    force_reanalysis: bool = False
    since_timestamp: Optional[datetime] = None
    
    model_config = ConfigDict(extra="forbid")

class SyncOperationOut(BaseModel):
    """Output DTO for sync operation"""
    id: UUID
    shop_id: str
    sync_type: str
    status: str
    total_products: int
    processed_products: int
    failed_products: int
    images_cached: int
    analysis_requested: int
    analysis_completed: int
    bulk_operation_id: Optional[str]
    since_timestamp: Optional[datetime]
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)

class SyncProgressOut(BaseModel):
    """Sync progress details"""
    total_products: int
    processed_products: int
    images_cached: int
    analysis_completed: int
    estimated_completion: Optional[datetime] = None