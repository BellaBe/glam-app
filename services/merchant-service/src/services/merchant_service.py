# services/merchant-service/src/services/merchant_service.py
from prisma.enums import MerchantStatus

from shared.messaging.events.base import MerchantIdentifiers
from shared.messaging.events.merchant import MerchantCreatedPayload
from shared.utils.logger import ServiceLogger

from ..events.publishers import MerchantEventPublisher
from ..exceptions import InvalidStatusTransitionError, MerchantNotFoundError
from ..repositories.merchant_repository import MerchantRepository
from ..schemas.merchant import (
    MerchantSelfOut,
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
            f"Syncing merchant: {data.domain}",
            extra={
                "correlation_id": ctx.correlation_id,
                "domain": data.domain,
                "platform_shop_id": data.platform_shop_id,
            },
        )

        # Find existing merchant
        existing = await self.repository.find_by_platform_shop_identity(
            platform_name=data.platform_name, domain=data.domain, platform_shop_id=data.platform_shop_id
        )

        if not existing:
            # Create new merchant
            merchant = await self.repository.create(data)
            created = True

            self.logger.info(
                f"Created new merchant: {merchant.domain}",
                extra={"merchant_id": merchant.id, "domain": merchant.domain},
            )

            payload = MerchantCreatedPayload(
                identifiers=MerchantIdentifiers(
                    merchant_id=merchant.id,
                    platform_name=merchant.platform_name,
                    platform_shop_id=merchant.platform_shop_id,
                    domain=merchant.domain,
                ),
                shop_name=merchant.name,
                email=merchant.email,
                country=merchant.country,
                currency=merchant.currency,
                timezone=merchant.timezone,
                platform_version=merchant.platform_version,
                scopes=merchant.scopes,
                status=merchant.status,
            )

            # Publish installed event
            await self.publisher.publish_merchant_created(
                payload=payload,
                correlation_id=ctx.correlation_id,
            )

        else:
            self.logger.warning("Implement reinstallation or sync logic", extra={"domain": data.domain})
            pass  # TODO: handle merchant scopes updates, profile updates, reinstallation, etc.

        return MerchantSyncOut(created=created, merchant_id=merchant.id)

    async def get_merchant_by_domain(self, domain: str) -> MerchantSelfOut:
        """Get merchant by platform domain"""
        merchant = await self.repository.find_by_domain(domain)
        if not merchant:
            raise MerchantNotFoundError(f"Merchant not found: {domain}")

        return MerchantSelfOut(
            id=merchant.id,
            platform_shop_id=merchant.platform_shop_id,
            domain=merchant.domain,
            shop_name=merchant.name,
            status=merchant.status,
        )

    async def update_merchant_status(self, domain: str, new_status: MerchantStatus) -> None:
        """Update merchant status (called by event listeners)"""

        merchant = await self.repository.find_by_domain(domain)
        if not merchant:
            raise MerchantNotFoundError(f"Merchant not found: {domain}")

        old_status = merchant.status

        # Validate transition
        if new_status not in STATUS_TRANSITIONS.get(old_status, []):
            self.logger.warning(
                f"Invalid status transition from {old_status} to {new_status}",
                extra={"merchant_id": merchant.id, "domain": domain},
            )
            raise InvalidStatusTransitionError(f"Invalid status transition from {old_status} to {new_status}")

        # Update status
        await self.repository.update_status(merchant.id, new_status)

    async def handle_app_uninstalled(self, domain: str, uninstall_reason: str | None = None) -> None:
        """Handle app uninstalled event"""
        self.logger.info(f"Handling app uninstall for {domain}", extra={"domain": domain})

        merchant = await self.repository.find_by_domain(domain)
        if not merchant:
            self.logger.warning(f"Merchant not found for uninstall: {domain}")
            return

        await self.repository.update_status(merchant.id, MerchantStatus.UNINSTALLED)
