# services/webhook-service/src/repositories/webhook_repository.py
from typing import Tuple, Optional, Any
from prisma import Prisma
from prisma.errors import UniqueViolationError
from ..models.enums import WebhookStatus

class WebhookRepository:
    def __init__(self, prisma: Prisma):
        self.prisma = prisma

    async def create_or_get_existing(
        self,
        *,
        platform: str,
        webhook_id: str,
        topic: str,
        shop_domain: str,
        payload: dict,
    ) -> Tuple[Any, bool]:
        """
        Create webhook or return existing. Returns (webhook, is_new).
        """
        # Check if exists
        existing = await self.prisma.webhookentry.find_unique(
            where={"webhook_id": webhook_id}
        )
        
        if existing:
            return existing, False
        
        # Create new
        try:
            webhook = await self.prisma.webhookentry.create(
                data={
                    "platform": platform,
                    "webhook_id": webhook_id,
                    "topic": topic,
                    "shop_domain": shop_domain.lower(),
                    "payload": payload,
                    "status": WebhookStatus.RECEIVED.value,
                }
            )
            return webhook, True
        except UniqueViolationError:
            # Race condition - another request created it
            existing = await self.prisma.webhookentry.find_unique(
                where={"webhook_id": webhook_id}
            )
            return existing, False

    async def update_status(
        self,
        id: str,
        status: WebhookStatus,
        error_message: Optional[str] = None,
    ):
        """Update webhook processing status"""
        from datetime import datetime
        
        update_data = {"status": status.value}
        
        if status == WebhookStatus.PROCESSED:
            update_data["processed_at"] = datetime.utcnow()
        
        if error_message:
            update_data["error_message"] = error_message
            
        return await self.prisma.webhookentry.update(
            where={"id": id},
            data=update_data
        )

    async def increment_attempts(self, id: str):
        """Increment processing attempts counter"""
        return await self.prisma.webhookentry.update(
            where={"id": id},
            data={"processing_attempts": {"increment": 1}}
        )