# services/merchant-service/src/events/publishers.py
from datetime import UTC, datetime

from prisma.enums import MerchantStatus

from shared.messaging.publisher import Publisher

from ..schemas.merchant import MerchantStatusUpdatedPayload, MerchantSyncedPayload


class MerchantEventPublisher(Publisher):
    """Publisher for merchant domain events"""

    @property
    def service_name(self) -> str:
        return "merchant-service"

    async def publish_merchant_created(
        self,
        correlation_id: str,
        merchant_id: str,
        platform_name: str,
        platform_shop_id: str,
        shop_domain: str,
        name: str,
        email: str,
        installed_at: datetime,
    ) -> str:
        """Publish evt.merchant.installed event"""

        self.logger.info(
            "Publishing merchant installed event",
            extra={"correlation_id": correlation_id, "merchant_id": merchant_id, "shop_domain": shop_domain},
        )

        return await self.publish_event(
            subject="evt.merchant.created.v1",
            data={
                "merchant_id": merchant_id,
                "platform_name": platform_name,
                "platform_shop_id": platform_shop_id,
                "shop_domain": shop_domain,
                "name": name,
                "email": email,
                "installed_at": installed_at.isoformat(),
            },
            correlation_id=correlation_id,
        )

    async def publish_merchant_reinstalled(
        self, correlation_id: str, merchant_id: str, platform_shop_id: str, shop_domain: str, name: str, email: str
    ) -> str:
        """Publish evt.merchant.reinstalled event"""
        return await self.publish_event(
            subject="evt.merchant.reinstalled.v1",
            data={
                "merchant_id": merchant_id,
                "platform_shop_id": platform_shop_id,
                "shop_domain": shop_domain,
                "name": name,
                "email": email,
                "reinstalled_at": datetime.utcnow().isoformat(),
            },
            correlation_id=correlation_id,
        )

    async def publish_merchant_synced(self, correlation_id: str, payload: MerchantSyncedPayload) -> str:
        """Publish evt.merchant.synced event"""
        return await self.publish_event(
            subject="evt.merchant.synced.v1", data=payload.model_dump(), correlation_id=correlation_id
        )

    async def publish_status_changed(
        self,
        correlation_id: str,  # REQUIRED
        old_status: MerchantStatus,
        payload: MerchantStatusUpdatedPayload,
    ) -> str:
        """Publish evt.merchant.status.changed event"""
        return await self.publish_event(
            subject="evt.merchant.status.changed.v1",
            data={**payload.model_dump(), "old_status": old_status.value, "changed_at": datetime.now(UTC).isoformat()},
            correlation_id=correlation_id,
        )
