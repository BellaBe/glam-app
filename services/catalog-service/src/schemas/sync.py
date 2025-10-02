# services/catalog-service/src/schemas/sync.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# Request bodies
class SyncRequestBody(BaseModel):
    """Request body for starting sync"""

    sync_type: str = Field(default="full", pattern="^(full|incremental)$")

    model_config = ConfigDict(extra="forbid")


# DTOs
class SyncOperationCreate(BaseModel):
    """DTO for creating sync operation"""

    merchant_id: str
    platform_name: str
    platform_shop_id: str
    domain: str
    sync_type: str = "full"


class SyncOperationOut(BaseModel):
    """DTO for sync operation response"""

    id: str
    merchant_id: str
    platform_name: str
    platform_shop_id: str
    domain: str
    sync_type: str
    status: str
    total_products: int
    processed_products: int
    failed_products: int
    analysis_completed: int
    progress_percent: int
    progress_message: str | None
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None

    model_config = ConfigDict(from_attributes=True)


class SyncProgressOut(BaseModel):
    """DTO for sync progress polling"""

    sync_id: str
    status: str
    progress_percent: int
    message: str
    total_products: int
    processed_products: int
    failed_products: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
