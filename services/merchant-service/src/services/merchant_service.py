# services/merchant-service/src/services/merchant_service.py
from prisma.enums import MerchantStatus

from shared.utils.logger import ServiceLogger

from ..events.publishers import MerchantEventPublisher
from ..exceptions import InvalidStatusTransitionError, MerchantNotFoundError
from ..repositories.merchant_repository import MerchantRepository
from ..schemas.merchant import (
    MerchantSelfOut,
    MerchantStatusUpdatedPayload,
    MerchantSyncedPayload,
    MerchantSyncIn,
    MerchantSyncOut,
)

# Status transition rules
STATUS_TRANSITIONS = {
    MerchantStatus.PENDING: [MerchantStatus.ACTIVE, MerchantStatus.UNINSTALLED],
    MerchantStatus.ACTIVE: [MerchantStatus.PAUSED, MerchantStatus.SUSPENDED, MerchantStatus.UNINSTALLED],
    MerchantStatus.PAUSED: [MerchantStatus.ACTIVE, MerchantStatus.SUSPENDED, MerchantStatus.UNINSTALLED],
    MerchantStatus.SUSPENDED: [MerchantStatus.ACTIVE, MerchantStatus.PAUSED, MerchantStatus.UNINSTALLED],
    MerchantStatus.UNINSTALLED: [MerchantStatus.PENDING],
}


class MerchantService:
    """Business logic for merchant operations"""

    def __init__(self, repository: MerchantRepository, publisher: MerchantEventPublisher, logger: ServiceLogger):
        self.repository = repository
        self.publisher = publisher
        self.logger = logger

    async def sync_merchant(self, data: MerchantSyncIn, ctx) -> MerchantSyncOut:
        """Sync merchant from OAuth flow"""

        self.logger.info(
            f"Syncing merchant: {data.shop_domain}",
            extra={
                "correlation_id": ctx.correlation_id,
                "shop_domain": data.shop_domain,
                "platform_shop_id": data.platform_shop_id,
            },
        )

        # Find existing merchant
        existing = await self.repository.find_by_platform_shop_identity(
            platform_name=data.platform_name, shop_domain=data.shop_domain, platform_shop_id=data.platform_shop_id
        )

        if existing:
            # Update existing merchant
            merchant = await self.repository.update_for_sync(existing.id, data)
            created = False

            # If merchant was uninstalled, set back to PENDING
            if merchant.status == MerchantStatus.UNINSTALLED:
                merchant = await self.repository.update_status(merchant.id, MerchantStatus.PENDING)

                # Publish reinstalled event
                await self.publisher.publish_merchant_reinstalled(
                    correlation_id=ctx.correlation_id,
                    merchant_id=merchant.id,
                    platform_shop_id=merchant.platform_shop_id,
                    shop_domain=merchant.shop_domain,
                    name=merchant.name,
                    email=merchant.email,
                )
        else:
            # Create new merchant
            merchant = await self.repository.create(data)
            created = True

            self.logger.info(
                f"Created new merchant: {merchant.shop_domain}",
                extra={"merchant_id": merchant.id, "shop_domain": merchant.shop_domain},
            )

            # Publish installed event
            await self.publisher.publish_merchant_created(
                correlation_id=ctx.correlation_id,
                merchant_id=merchant.id,
                platform_name=merchant.platform_name,
                platform_shop_id=merchant.platform_shop_id,
                shop_domain=merchant.shop_domain,
                name=merchant.name,
                email=merchant.email,
                installed_at=merchant.installed_at,
            )

        # Always publish synced event
        synced_payload = MerchantSyncedPayload(
            merchant_id=merchant.id,
            platform_name=merchant.platform_name,
            platform_shop_id=merchant.platform_shop_id,
            shop_domain=merchant.shop_domain,
            contact_email=merchant.email,
            name=merchant.name,
            status=merchant.status,
        )

        await self.publisher.publish_merchant_synced(correlation_id=ctx.correlation_id, payload=synced_payload)

        return MerchantSyncOut(created=created, merchant_id=merchant.id)

    async def get_merchant_by_domain(self, shop_domain: str) -> MerchantSelfOut:
        """Get merchant by platform domain"""
        merchant = await self.repository.find_by_shop_domain(shop_domain)
        if not merchant:
            raise MerchantNotFoundError(f"Merchant not found: {shop_domain}")

        return MerchantSelfOut(
            id=merchant.id,
            platform_shop_id=merchant.platform_shop_id,
            shop_domain=merchant.shop_domain,
            shop_name=merchant.name,
            status=merchant.status,
        )

    async def update_merchant_status(self, shop_domain: str, new_status: MerchantStatus) -> None:
        """Update merchant status (called by event listeners)"""

        merchant = await self.repository.find_by_shop_domain(shop_domain)
        if not merchant:
            raise MerchantNotFoundError(f"Merchant not found: {shop_domain}")

        old_status = merchant.status

        # Validate transition
        if new_status not in STATUS_TRANSITIONS.get(old_status, []):
            self.logger.warning(
                f"Invalid status transition from {old_status} to {new_status}",
                extra={"merchant_id": merchant.id, "shop_domain": shop_domain},
            )
            raise InvalidStatusTransitionError(f"Invalid status transition from {old_status} to {new_status}")

        # Update status
        await self.repository.update_status(merchant.id, new_status)

        # Publish status changed event
        status_payload = MerchantStatusUpdatedPayload(
            merchant_id=merchant.id,
            platform_shop_id=merchant.platform_shop_id,
            shop_domain=merchant.shop_domain,
            status=new_status,
        )

        await self.publisher.publish_status_changed(
            correlation_id=merchant.correlation_id,  # TODO: set a propper ctx Assuming this is available in the context
            old_status=old_status,
            payload=status_payload,
        )

    async def handle_app_uninstalled(self, shop_domain: str, uninstall_reason: str | None = None) -> None:
        """Handle app uninstalled event"""
        self.logger.info(f"Handling app uninstall for {shop_domain}", extra={"shop_domain": shop_domain})

        merchant = await self.repository.find_by_shop_domain(shop_domain)
        if not merchant:
            self.logger.warning(f"Merchant not found for uninstall: {shop_domain}")
            return

        # Update status to UNINSTALLED
        await self.repository.update_status(merchant.id, MerchantStatus.UNINSTALLED)

        # Publish uninstalled event
        await self.publisher.publish_merchant_uninstalled(
            correlation_id=merchant.correlation_id,  # TODO: set a propper ctx Assuming this is available in the context
            merchant_id=merchant.id,
            platform_shop_id=merchant.platform_shop_id,
            shop_domain=merchant.shop_domain,
            name=merchant.name,
            email=merchant.email,
            uninstall_reason=uninstall_reason,
        )
