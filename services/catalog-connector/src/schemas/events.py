# services/platform-connector/src/schemas/events.py
from typing import Optional
from pydantic import BaseModel

class CatalogSyncRequestedPayload(BaseModel):
    """Payload for catalog.sync.requested event"""
    merchant_id: str
    platform_name: str
    platform_id: str
    platform_domain: str
    sync_id: str
    sync_type: str = "full"