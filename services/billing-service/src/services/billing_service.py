from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..db.models import PaymentStatus
from ..exceptions import (
    InvalidPlatformError,
    MerchantNotFoundError,
    PaymentNotFoundError,
    PlatformChargeError,
    ProductInactiveError,
    ProductNotFoundError,
    TrialAlreadyActivatedError,
)
from ..repositories.billing_repository import (
    BillingAccountRepository,
    PaymentRepository,
    ProductRepository,
)
from ..schemas.billing import (
    CreateChargeIn,
    CreateChargeOut,
    PaymentOut,
    ProductOut,
    TrialStatusOut,
)


class BillingService:
    TRIAL_CREDITS = 500
    PAYMENT_EXPIRY_HOURS = 24

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        publisher,  # BillingEventPublisher
        platform_adapter,  # ShopifyAdapter
        logger,
    ):
        self.session_factory = session_factory
        self.publisher = publisher
        self.platform_adapter = platform_adapter
        self.logger = logger

    async def handle_merchant_created(
        self,
        merchant_id: str,
        platform_name: str,
        platform_id: str,
        platform_domain: str,
        correlation_id: str,
    ) -> None:
        """Handle merchant created event - create billing account"""
        async with self.session_factory() as session:
            repo = BillingAccountRepository(session)

            # Check idempotency
            existing = await repo.find_by_merchant_id(merchant_id)
            if existing:
                self.logger.info(f"Billing account already exists for {merchant_id}")
                return

            # Create account
            await repo.create(
                merchant_id=merchant_id,
                platform_name=platform_name,
                platform_shop_id=platform_id,
                platform_domain=platform_domain,
            )
            await session.commit()

            # Emit event
            await self.publisher.billing_record_created(
                merchant_id=UUID(merchant_id),
                platform_name=platform_name,
                platform_id=platform_id,
                platform_domain=platform_domain,
                correlation_id=correlation_id,
            )

            self.logger.info(f"Billing account created for {merchant_id}")

    async def get_trial_status(self, merchant_id: str) -> TrialStatusOut:
        """Get trial status for merchant"""
        async with self.session_factory() as session:
            repo = BillingAccountRepository(session)
            account = await repo.find_by_merchant_id(merchant_id)

            if not account:
                raise MerchantNotFoundError(message=f"Merchant not found: {merchant_id}")

            return TrialStatusOut(
                available=account.trial_available,
                activated_at=account.trial_activated_at,
            )

    async def activate_trial(
        self,
        merchant_id: str,
        correlation_id: str,
    ) -> None:
        """Activate trial for merchant"""
        async with self.session_factory() as session:
            repo = BillingAccountRepository(session)
            account = await repo.find_by_merchant_id(merchant_id)

            if not account:
                raise MerchantNotFoundError(message=f"Merchant not found: {merchant_id}")

            if not account.trial_available:
                raise TrialAlreadyActivatedError(message="Trial already activated")

            # Activate
            await repo.activate_trial(merchant_id)
            await session.commit()

            # Emit grant event
            await self.publisher.trial_activated(
                merchant_id=UUID(merchant_id),
                grant_amount=self.TRIAL_CREDITS,
                correlation_id=correlation_id,
            )

            self.logger.info(f"Trial activated for {merchant_id}")

    async def list_products(self) -> list[ProductOut]:
        """List active pricing products"""
        async with self.session_factory() as session:
            repo = ProductRepository(session)
            products = await repo.list_active()
            return [ProductOut.model_validate(p) for p in products]

    async def create_charge(
        self,
        merchant_id: str,
        data: CreateChargeIn,
        correlation_id: str,
    ) -> CreateChargeOut:
        """Create payment charge"""
        async with self.session_factory() as session:
            account_repo = BillingAccountRepository(session)
            product_repo = ProductRepository(session)
            payment_repo = PaymentRepository(session)

            # Get account
            account = await account_repo.find_by_merchant_id(merchant_id)
            if not account:
                raise MerchantNotFoundError(message=f"Merchant not found: {merchant_id}")

            # Get product
            product = await product_repo.find_by_id(data.product_id)
            if not product:
                raise ProductNotFoundError(message=f"Product not found: {data.product_id}")

            if not product.active:
                raise ProductInactiveError(message="Product not available")

            # Validate platform
            if data.platform not in ["shopify"]:
                raise InvalidPlatformError(message=f"Platform not supported: {data.platform}")

            # Create payment record
            payment = await payment_repo.create(
                merchant_id=merchant_id,
                amount=product.price,
                currency=product.currency,
                description=f"{product.name.title()} Credit Pack ({product.metadata['credits']} credits)",
                product_type=product.type,
                product_id=product.id,
                platform_name=data.platform,
                metadata={
                    "credits": product.metadata["credits"],
                    "pack_name": product.name,
                },
                expires_at=datetime.now(UTC) + timedelta(hours=self.PAYMENT_EXPIRY_HOURS),
            )
            await session.commit()

            # Create platform charge
            try:
                checkout_url = await self.platform_adapter.create_charge(
                    account=account,
                    payment=payment,
                    product=product,
                    return_url=data.return_url,
                )
            except Exception as e:
                self.logger.error(f"Platform charge creation failed: {e}", exc_info=True)
                raise PlatformChargeError("Failed to create platform charge") from e

            self.logger.info(f"Created charge {payment.id} for merchant {merchant_id}")

            return CreateChargeOut(
                payment_id=UUID(payment.id),
                checkout_url=checkout_url,
            )

    async def get_payment(self, payment_id: str) -> PaymentOut:
        """Get payment by ID"""
        async with self.session_factory() as session:
            repo = PaymentRepository(session)
            payment = await repo.find_by_id(payment_id)

            if not payment:
                raise PaymentNotFoundError(message=f"Payment not found: {payment_id}")

            return PaymentOut.model_validate(payment)

    async def list_payments(
        self,
        merchant_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PaymentOut]:
        """List payments for merchant"""
        async with self.session_factory() as session:
            repo = PaymentRepository(session)
            payments = await repo.list_by_merchant(
                merchant_id=merchant_id,
                limit=limit,
                offset=offset,
            )
            return [PaymentOut.model_validate(p) for p in payments]

    async def handle_purchase_updated(
        self,
        charge_id: str,
        status: str,
        correlation_id: str,
    ) -> None:
        """Handle purchase webhook - update payment status"""
        async with self.session_factory() as session:
            payment_repo = PaymentRepository(session)
            account_repo = BillingAccountRepository(session)

            # Find payment
            payment = await payment_repo.find_by_platform_charge_id(charge_id)
            if not payment:
                self.logger.error(f"Payment not found for charge {charge_id}")
                return

            # Already processed?
            if payment.status != PaymentStatus.PENDING:
                self.logger.info(f"Payment {payment.id} already processed")
                return

            # Update based on status
            if status == "accepted":
                # Mark completed
                await payment_repo.mark_completed(payment.id)

                # Update account spending
                await account_repo.update_spend(
                    merchant_id=payment.merchant_id,
                    amount=payment.amount,
                )
                await session.commit()

                # Emit success event
                await self.publisher.purchase_completed(
                    merchant_id=UUID(payment.merchant_id),
                    payment_id=UUID(payment.id),
                    product_id=payment.product_id,
                    amount=float(payment.amount),
                    currency=payment.currency,
                    metadata=payment.metadata or {},
                    correlation_id=correlation_id,
                )

                self.logger.info(f"Payment {payment.id} completed")
            else:
                # Mark failed
                await payment_repo.mark_failed(payment.id)
                await session.commit()

                # Emit failure event
                await self.publisher.purchase_failed(
                    merchant_id=UUID(payment.merchant_id),
                    payment_id=UUID(payment.id),
                    reason=status,
                    correlation_id=correlation_id,
                )

                self.logger.info(f"Payment {payment.id} failed: {status}")

    async def handle_purchase_refunded(
        self,
        charge_id: str,
        correlation_id: str,
    ) -> None:
        """Handle purchase refund webhook"""
        async with self.session_factory() as session:
            payment_repo = PaymentRepository(session)

            # Find payment
            payment = await payment_repo.find_by_platform_charge_id(charge_id)
            if not payment:
                self.logger.error(f"Payment not found for charge {charge_id}")
                return

            # Mark refunded
            await payment_repo.mark_refunded(payment.id)
            await session.commit()

            # Emit refund event
            await self.publisher.purchase_refunded(
                merchant_id=UUID(payment.merchant_id),
                payment_id=UUID(payment.id),
                amount=float(payment.amount),
                metadata=payment.metadata or {},
                correlation_id=correlation_id,
            )

            self.logger.info(f"Payment {payment.id} refunded")

    async def cleanup_expired_payments(self) -> int:
        """Mark expired pending payments"""
        async with self.session_factory() as session:
            repo = PaymentRepository(session)
            count = await repo.mark_expired_payments()
            await session.commit()

            self.logger.info(f"Marked {count} payments as expired")
            return count
