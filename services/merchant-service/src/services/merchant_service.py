from __future__ import annotations
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.models import Merchant, MerchantStatus, STATUS_TRANSITIONS
from src.repositories.merchant_repository import MerchantRepository
from src.schemas.merchant import MerchantSyncIn, MerchantOut, MerchantSyncResponse
from src.events.publishers import MerchantEventPublisher
from src.exceptions import (
    MerchantNotFoundError,
    InvalidStatusTransitionError
)
from shared.utils.logger import ServiceLogger


class MerchantService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        publisher: MerchantEventPublisher,
        logger: ServiceLogger
    ):
        self.session_factory = session_factory
        self.publisher = publisher
        self.logger = logger

    async def sync_merchant(
        self,
        platform_name: str,
        data: MerchantSyncIn,
        correlation_id: str
    ) -> MerchantSyncResponse:
        """Sync merchant from platform OAuth flow"""
        async with self.session_factory() as session:
            repo = MerchantRepository(session)
            
            # Try to find existing merchant
            existing = await repo.find_by_platform_and_domain(
                platform_name,
                data.domain
            )

            if existing:
                # Update existing merchant
                merchant = await repo.update_from_sync(existing, data)
                await session.commit()
                created = False
                
                self.logger.info(
                    f"Merchant synced: {merchant.domain}",
                    extra={
                        "merchant_id": merchant.id,
                        "platform": platform_name,
                        "reinstall": existing.status == MerchantStatus.UNINSTALLED
                    }
                )
            else:
                # Create new merchant
                merchant = await repo.create(platform_name, data)
                await session.commit()
                created = True
                
                self.logger.info(
                    f"Merchant created: {merchant.domain}",
                    extra={
                        "merchant_id": merchant.id,
                        "platform": platform_name
                    }
                )

            # Convert to output schema
            merchant_out = MerchantOut.model_validate(merchant)

            # Publish events
            if created:
                await self.publisher.merchant_created(
                    merchant_out,
                    correlation_id
                )

            await self.publisher.merchant_synced(
                merchant_out,
                first_install=created,
                correlation_id=correlation_id
            )

            return MerchantSyncResponse(
                created=created,
                merchant_id=UUID(merchant.id)
            )

    async def get_merchant(
        self,
        platform_name: str,
        domain: str
    ) -> MerchantOut:
        """Get merchant by platform and domain"""
        async with self.session_factory() as session:
            repo = MerchantRepository(session)
            merchant = await repo.find_by_platform_and_domain(
                platform_name,
                domain
            )

            if not merchant:
                raise MerchantNotFoundError(
                    message=f"Merchant not found: {domain}"
                )

            return MerchantOut.model_validate(merchant)

    async def handle_app_uninstalled(
        self,
        platform_name: str,
        domain: str,
        correlation_id: str
    ) -> None:
        """Handle app uninstalled event from webhook service"""
        async with self.session_factory() as session:
            repo = MerchantRepository(session)
            merchant = await repo.find_by_platform_and_domain(
                platform_name,
                domain
            )

            if not merchant:
                self.logger.warning(
                    f"Uninstall event for unknown merchant: {domain}",
                    extra={"platform": platform_name, "domain": domain}
                )
                return

            old_status = merchant.status
            merchant = await repo.update_status(
                merchant,
                MerchantStatus.UNINSTALLED
            )
            await session.commit()

            self.logger.info(
                f"Merchant uninstalled: {domain}",
                extra={
                    "merchant_id": merchant.id,
                    "platform": platform_name,
                    "old_status": old_status
                }
            )

            # Publish uninstalled event
            await self.publisher.merchant_uninstalled(
                merchant_id=UUID(merchant.id),
                platform_name=merchant.platform_name,
                platform_shop_id=merchant.platform_shop_id,
                domain=merchant.domain,
                uninstalled_at=merchant.uninstalled_at,
                correlation_id=correlation_id
            )

            # Publish status changed event
            await self.publisher.merchant_status_changed(
                merchant_id=UUID(merchant.id),
                platform_name=merchant.platform_name,
                platform_shop_id=merchant.platform_shop_id,
                domain=merchant.domain,
                old_status=old_status.value,
                new_status=MerchantStatus.UNINSTALLED.value,
                correlation_id=correlation_id
            )

    def validate_status_transition(
        self,
        current_status: MerchantStatus,
        new_status: MerchantStatus
    ) -> None:
        """Validate status transition"""
        allowed = STATUS_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise InvalidStatusTransitionError(
                f"Invalid status transition from {current_status} to {new_status}"
            )