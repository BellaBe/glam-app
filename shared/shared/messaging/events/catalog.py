# shared/shared/messaging/events/catalog.py

from uuid import UUID

from pydantic import Field

from shared.messaging.events.base import BaseEventPayload


class CatalogSyncStartedPayload(BaseEventPayload):
    """Payload for catalog sync started event"""

    sync_id: UUID = Field(..., description="Unique sync operation ID")
    total_items: int = Field(..., description="Total items to sync")
    status: str = Field(..., description="Initial sync status")


class CatalogSyncCompletedPayload(BaseEventPayload):
    """Payload for catalog sync completed event"""

    sync_id: UUID = Field(..., description="Unique sync operation ID")
    total_items: int = Field(..., description="Total items synced")
    status: str = Field(..., description="Final sync status")
    first_sync: bool = Field(default=False, description="Is this the first sync?")
    has_changes: bool = Field(default=False, description="Were there any changes?")
    email: str | None = Field(None, description="Merchant email if available")
