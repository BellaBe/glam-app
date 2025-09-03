# services/platform-connector/src/schemas/events.py
from pydantic import BaseModel


class CatalogSyncRequestedPayload(BaseModel):
    """Payload for catalog.sync.requested event"""

    merchant_id: str
    platform_name: str
    platform_shop_id: str
    domain: str
    sync_id: str
    sync_type: str = "full"
