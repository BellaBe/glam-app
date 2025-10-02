# services/merchant-service/src/services/merchant_service.py
from prisma.enums import MerchantStatus

from shared.messaging.events.base import MerchantIdentifiers
from shared.utils.logger import ServiceLogger

from ..events.publishers import MerchantEventPublisher
from ..repositories.merchant_repository import MerchantRepository
from ..schemas.merchant import MerchantOut, MerchantSyncIn, MerchantSyncOut

# Optional: guard rails for internal transitions
STATUS_TRANSITIONS = {
    MerchantStatus.PENDING: [MerchantStatus.ACTIVE, MerchantStatus.UNINSTALLED],
    MerchantStatus.ACTIVE: [MerchantStatus.PAUSED, MerchantStatus.SUSPENDED, MerchantStatus.UNINSTALLED],
    MerchantStatus.PAUSED: [MerchantStatus.ACTIVE, MerchantStatus.SUSPENDED, MerchantStatus.UNINSTALLED],
    MerchantStatus.SUSPENDED: [MerchantStatus.ACTIVE, MerchantStatus.PAUSED, MerchantStatus.UNINSTALLED],
    MerchantStatus.UNINSTALLED: [MerchantStatus.PENDING],
}


class MerchantService:
    """Business logic for merchant operations."""

    def __init__(self, repository: MerchantRepository, publisher: MerchantEventPublisher, logger: ServiceLogger):
        self.repository = repository
        self.publisher = publisher
        self.logger = logger

    async def sync_merchant(self, data: MerchantSyncIn, platform_name: str, domain: str, ctx) -> MerchantSyncOut:
        """
        Sync handler (create or update) invoked by BFF after-auth.
        Rules:
          - If merchant doesn't exist: create (status=PENDING), emit created, emit synced.
          - If exists & status=UNINSTALLED: mark reinstalled (status=PENDING, installed_at=now),
            update profile + last_synced_at, emit reinstalled, emit synced.
          - Else: update profile + last_synced_at, emit synced.
        """
        m = await self.repository.find_by_platform_identity(
            platform_name=platform_name, domain=domain, platform_shop_id=data.platform_shop_id
        )

        if not m:
            m = await self.repository.create(platform_name=platform_name, domain=domain, data=data)
            identifiers = MerchantIdentifiers(
                merchant_id=m.id, platform_name=m.platform_name, platform_shop_id=m.platform_shop_id, domain=m.domain
            )
            # publish created + synced (flat snapshot inside publisher)
            await self.publisher.merchant_created(m, ctx)
            return MerchantSyncOut(success=True)

        # reinstall path
        if m.status == MerchantStatus.UNINSTALLED:
            m = await self.repository.mark_reinstalled(merchant_id=m.id)
            # Then sync details
            m = await self.repository.update_for_sync(merchant_id=m.id, data=data)
            identifiers = MerchantIdentifiers(
                merchant_id=m.id, platform_name=m.platform_name, platform_shop_id=m.platform_shop_id, domain=m.domain
            )
            await self.publisher.merchant_reinstalled(m, ctx)
            return MerchantSyncOut(success=True)

        # normal sync path
        m = await self.repository.update_for_sync(merchant_id=m.id, data=data)
        identifiers = MerchantIdentifiers(
            merchant_id=m.id, platform_name=m.platform_name, platform_shop_id=m.platform_shop_id, domain=m.domain
        )
        await self.publisher.merchant_synced(m, ctx)
        return MerchantSyncOut(success=True)

    async def update_merchant_status(self, identifiers: MerchantIdentifiers, new_status: MerchantStatus) -> None:
        """
        Update status (called by internal logic listeners).
        Emits `merchant.status_changed` when state actually changes.
        """
        m = await self.repository.find_by_platform_identity(
            platform_name=identifiers.platform_name,
            domain=identifiers.domain,
            platform_shop_id=identifiers.platform_shop_id,
        )
        if not m:
            self.logger.warning("Update status: merchant not found", extra=identifiers.model_dump())
            return

        if m.status == new_status:
            return  # no-op

        allowed = STATUS_TRANSITIONS.get(m.status, [])
        if new_status not in allowed:
            self.logger.warning(
                "Invalid status transition",
                extra={"from": m.status, "to": new_status, "merchant_id": str(m.id)},
            )
            return

        m = await self.repository.update_status(merchant_id=m.id, new_status=new_status)
        await self.publisher.merchant_status_changed(identifiers, m)

    async def handle_app_uninstalled(self, platform_name: str, domain: str) -> None:
        """
        Uninstall from webhook event listener:
          - Find by identity
          - Set status=UNINSTALLED, uninstalled_at=now
          - Emit merchant.uninstalled
        """
        m = await self.repository.find_by_platform_identity(
            platform_name=platform_name, domain=domain, platform_shop_id=None
        )
        if not m:
            self.logger.warning(
                "Uninstall: merchant not found", extra={"platform_name": platform_name, "domain": domain}
            )
            return

        if m.status == MerchantStatus.UNINSTALLED:
            return  # idempotent

        m = await self.repository.mark_uninstalled(merchant_id=m.id)
        identifiers = MerchantIdentifiers(
            merchant_id=m.id, platform_name=m.platform_name, platform_shop_id=m.platform_shop_id, domain=m.domain
        )
        await self.publisher.merchant_uninstalled(identifiers, m)

    async def get_merchant(self, *, domain: str, platform_name: str) -> MerchantOut:
        m = await self.repository.find_by_platform_identity(
            platform_name=platform_name, domain=domain, platform_shop_id=None
        )
        if not m:
            from ..exceptions import MerchantNotFoundError

            raise MerchantNotFoundError(domain=domain, platform=platform_name)

        # Map ORM -> API schema
        return MerchantOut(
            id=m.id,
            platform_name=m.platform_name,
            platform_shop_id=m.platform_shop_id,
            domain=m.domain,
            name=m.name,
            email=m.email,
            primary_domain=m.primary_domain,
            currency=m.currency,
            country=m.country,
            platform_version=m.platform_version,
            scopes=m.scopes,
            status=m.status,
            last_synced_at=m.last_synced_at,
            created_at=m.created_at,
            updated_at=m.updated_at,
            installed_at=m.installed_at,
            uninstalled_at=m.uninstalled_at,
        )
