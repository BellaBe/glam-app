# services/merchant-service/src/events/publishers.py
from uuid import UUID
from datetime import datetime

from shared.messaging.publisher import Publisher
from shared.messaging.subjects import Subjects

from ..schemas.merchant import MerchantOut


class MerchantEventPublisher(Publisher):
    """Publisher for merchant domain events"""

    @property
    def service_name(self) -> str:
        return "merchant-service"

    async def merchant_created(
        self,
        merchant: MerchantOut,
        correlation_id: str
    ) -> str:
        """Publish merchant created event"""
        payload = {
            "merchant_id": str(merchant.id),
            "platform_name": merchant.platform_name,
            "platform_shop_id": merchant.platform_shop_id,
            "domain": merchant.domain,
            "name": merchant.name,
            "email": merchant.email,
            "primary_domain": merchant.primary_domain,
            "currency": merchant.currency,
            "country": merchant.country,
            "platform_version": merchant.platform_version,
            "scopes": merchant.scopes,
            "installed_at": merchant.installed_at.isoformat() if merchant.installed_at else None,
            "status": merchant.status,
            "correlation_id": correlation_id
        }

        return await self.publish_event(
            subject=Subjects.MERCHANT_CREATED,
            payload=payload,
            correlation_id=correlation_id
        )

    async def merchant_synced(
        self,
        merchant: MerchantOut,
        first_install: bool,
        correlation_id: str
    ) -> str:
        """Publish merchant synced event"""
        payload = {
            "merchant_id": str(merchant.id),
            "platform_name": merchant.platform_name,
            "platform_shop_id": merchant.platform_shop_id,
            "domain": merchant.domain,
            "first_install": first_install,
            "last_synced_at": merchant.last_synced_at.isoformat() if merchant.last_synced_at else None,
            "scopes": merchant.scopes,
            "correlation_id": correlation_id
        }

        return await self.publish_event(
            subject=Subjects.MERCHANT_SYNCED,
            payload=payload,
            correlation_id=correlation_id
        )

    async def merchant_status_changed(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_shop_id: str,
        domain: str,
        old_status: str,
        new_status: str,
        correlation_id: str
    ) -> str:
        """Publish merchant status changed event"""
        payload = {
            "merchant_id": str(merchant_id),
            "platform_name": platform_name,
            "platform_shop_id": platform_shop_id,
            "domain": domain,
            "old_status": old_status,
            "new_status": new_status,
            "changed_at": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id
        }

        return await self.publish_event(
            subject=Subjects.MERCHANT_STATUS_CHANGED,
            payload=payload,
            correlation_id=correlation_id
        )

    async def merchant_uninstalled(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_shop_id: str,
        domain: str,
        uninstalled_at: datetime,
        correlation_id: str
    ) -> str:
        """Publish merchant uninstalled event"""
        payload = {
            "merchant_id": str(merchant_id),
            "platform_name": platform_name,
            "platform_shop_id": platform_shop_id,
            "domain": domain,
            "uninstalled_at": uninstalled_at.isoformat(),
            "correlation_id": correlation_id
        }

        return await self.publish_event(
            subject=Subjects.MERCHANT_UNINSTALLED,
            payload=payload,
            correlation_id=correlation_id
        )
