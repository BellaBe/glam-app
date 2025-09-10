# services/merchant-service/src/events/publishers.py
from uuid import UUID

from shared.messaging.events.base import MerchantIdentifiers
from shared.messaging.events.merchant import (
    MerchantCreatedPayload,
    MerchantReinstalledPayload,
    MerchantStatusChangedPayload,
    MerchantSyncedPayload,
    MerchantUninstalledPayload,
)
from shared.messaging.publisher import Publisher
from shared.messaging.subjects import Subjects

from ..schemas.merchant import MerchantOut


class MerchantEventPublisher(Publisher):
    """Publisher for merchant domain events"""

    @property
    def service_name(self) -> str:
        return "merchant-service"

    async def merchant_created(self, merchant: MerchantOut, ctx) -> str:
        """Publish merchant created event"""

        identifiers = MerchantIdentifiers(
            merchant_id=UUID(merchant.id),
            platform_name=merchant.platform_name,
            platform_shop_id=merchant.platform_shop_id,
            domain=merchant.domain,
        )

        payload = MerchantCreatedPayload(
            identifiers=identifiers,
            name=merchant.name,
            email=merchant.email,
            primary_domain=merchant.primary_domain,
            currency=merchant.currency,
            country=merchant.country,
            platform_version=merchant.platform_version,
            scopes=merchant.scopes,
            status=merchant.status,
        )

        return await self.publish_event(
            subject=Subjects.MERCHANT_CREATED,
            payload=payload,
            correlation_id=ctx.correlation_id,
        )

    async def merchant_synced(
        self,
        merchant: MerchantOut,
        ctx,
    ) -> str:
        """Publish evt.merchant.synced event"""

        identifiers = MerchantIdentifiers(
            merchant_id=UUID(merchant.id),
            platform_name=merchant.platform_name,
            platform_shop_id=merchant.platform_shop_id,
            domain=merchant.domain,
        )

        payload = MerchantSyncedPayload(
            identifiers=identifiers,
            name=merchant.name,
            email=merchant.email,
            primary_domain=merchant.primary_domain,
            currency=merchant.currency,
            country=merchant.country,
            platform_version=merchant.platform_version,
            scopes=merchant.scopes,
        )

        return await self.publish_event(
            subject=Subjects.MERCHANT_SYNCED,
            payload=payload,
            correlation_id=ctx.correlation_id,
        )

    async def merchant_reinstalled(
        self,
        merchant: MerchantOut,
        ctx,
    ) -> str:
        """Publish evt.merchant.reinstalled event"""

        identifiers = MerchantIdentifiers(
            merchant_id=UUID(merchant.id),
            platform_name=merchant.platform_name,
            platform_shop_id=merchant.platform_shop_id,
            domain=merchant.domain,
        )

        payload = MerchantReinstalledPayload(
            identifiers=identifiers,
            name=merchant.name,
            email=merchant.email,
            primary_domain=merchant.primary_domain,
            currency=merchant.currency,
            country=merchant.country,
            platform_version=merchant.platform_version,
            scopes=merchant.scopes,
        )

        return await self.publish_event(
            subject=Subjects.MERCHANT_REINSTALLED,
            payload=payload,
            correlation_id=ctx.correlation_id,
        )

    async def merchant_uninstalled(
        self,
        identifiers: MerchantIdentifiers,
        updated_at,
        ctx,
    ) -> str:
        """Publish evt.merchant.uninstalled event"""

        payload = MerchantUninstalledPayload(
            identifiers=identifiers,
            updated_at=updated_at,
        )

        return await self.publish_event(
            subject=Subjects.MERCHANT_UNINSTALLED,
            payload=payload,
            correlation_id=ctx.correlation_id,
        )

    async def merchant_status_changed(
        self,
        identifiers: MerchantIdentifiers,
        from_status: str,
        to_status: str,
        merchant: MerchantOut,
        ctx,
    ) -> str:
        """Publish evt.merchant.status_changed event"""

        payload = MerchantStatusChangedPayload(
            identifiers=identifiers,
            from_status=from_status,
            to_status=to_status,
            name=merchant.name,
            email=merchant.email,
            primary_domain=merchant.primary_domain,
            currency=merchant.currency,
            country=merchant.country,
            platform_version=merchant.platform_version,
            scopes=merchant.scopes,
        )

        return await self.publish_event(
            subject=Subjects.MERCHANT_STATUS_CHANGED,
            payload=payload,
            correlation_id=ctx.correlation_id,
        )
