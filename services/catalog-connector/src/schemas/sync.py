# src/schemas/sync_request.py
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SyncFetchRequestIn(BaseModel):
    """Incoming sync fetch request from catalog service"""

    sync_id: UUID
    shop_id: str
    sync_type: str  # "full" or "incremental"
    options: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")


class BulkOperationOut(BaseModel):
    """Bulk operation status output"""

    id: UUID
    sync_id: UUID
    shop_id: str
    shopify_bulk_id: str
    status: str
    object_count: int | None
    file_size: int | None
    download_url: str | None
    error_code: str | None
    error_message: str | None
    retry_count: int
    started_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
