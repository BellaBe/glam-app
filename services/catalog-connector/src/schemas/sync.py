# src/schemas/sync_request.py
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any

class SyncFetchRequestIn(BaseModel):
    """Incoming sync fetch request from catalog service"""
    sync_id: UUID
    shop_id: str
    sync_type: str  # "full" or "incremental"
    options: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(extra="ignore")

class BulkOperationOut(BaseModel):
    """Bulk operation status output"""
    id: UUID
    sync_id: UUID
    shop_id: str
    shopify_bulk_id: str
    status: str
    object_count: Optional[int]
    file_size: Optional[int]
    download_url: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    retry_count: int
    started_at: datetime
    completed_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)
