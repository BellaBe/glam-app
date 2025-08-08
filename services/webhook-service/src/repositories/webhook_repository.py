from typing import Optional, List
from uuid import UUID
from datetime import datetime
from prisma import Prisma
from prisma.models import WebhookEntry
from ..models.enums import WebhookStatus
from ..schemas.webhook import WebhookEntryOut


class WebhookRepository:
    """Repository for webhook operations using Prisma"""
    
    def __init__(self, prisma: Prisma):
        self.prisma = prisma
    
    async def create(
        self,
        platform: str,
        topic_raw: str,
        topic_enum: str,
        shop_domain: str,
        webhook_id: str,
        api_version: Optional[str],
        signature: str,
        headers: dict,
        payload: dict,
        payload_bytes: Optional[int] = None
    ) -> WebhookEntryOut:
        """Create new webhook entry"""
        webhook = await self.prisma.webhookentry.create(
            data={
                "platform": platform,
                "topic_raw": topic_raw,
                "topic_enum": topic_enum,
                "shop_domain": shop_domain.lower(),  # Ensure lowercase
                "webhook_id": webhook_id,
                "api_version": api_version,
                "signature": signature,
                "headers": headers,
                "payload": payload,
                "payload_bytes": payload_bytes,
                "status": WebhookStatus.RECEIVED.value,
                "processing_attempts": 0,
            }
        )
        return WebhookEntryOut.model_validate(webhook)
    
    async def find_by_id(self, webhook_id: UUID) -> Optional[WebhookEntryOut]:
        """Find webhook by internal ID"""
        webhook = await self.prisma.webhookentry.find_unique(
            where={"id": str(webhook_id)}
        )
        return WebhookEntryOut.model_validate(webhook) if webhook else None
    
    async def find_by_webhook_id(self, webhook_id: str) -> Optional[WebhookEntryOut]:
        """Find webhook by platform webhook ID"""
        webhook = await self.prisma.webhookentry.find_unique(
            where={"webhook_id": webhook_id}
        )
        return WebhookEntryOut.model_validate(webhook) if webhook else None
    
    async def update_status(
        self,
        webhook_id: UUID,
        status: WebhookStatus,
        error_message: Optional[str] = None,
        processed_at: Optional[datetime] = None
    ) -> WebhookEntryOut:
        """Update webhook status"""
        update_data = {"status": status.value}
        if error_message is not None:
            update_data["error_message"] = error_message
        if processed_at is not None:
            update_data["processed_at"] = processed_at
            
        webhook = await self.prisma.webhookentry.update(
            where={"id": str(webhook_id)},
            data=update_data
        )
        return WebhookEntryOut.model_validate(webhook)
    
    async def increment_attempts(self, webhook_id: UUID) -> WebhookEntryOut:
        """Increment processing attempts"""
        webhook = await self.prisma.webhookentry.update(
            where={"id": str(webhook_id)},
            data={"processing_attempts": {"increment": 1}}
        )
        return WebhookEntryOut.model_validate(webhook)
    
    async def find_pending_webhooks(self, limit: int = 100) -> List[WebhookEntryOut]:
        """Find webhooks pending processing"""
        webhooks = await self.prisma.webhookentry.find_many(
            where={
                "status": {"in": [WebhookStatus.RECEIVED.value, WebhookStatus.PROCESSING.value]},
                "processing_attempts": {"lt": 10}
            },
            order_by={"created_at": "asc"},
            take=limit
        )
        return [WebhookEntryOut.model_validate(w) for w in webhooks]


