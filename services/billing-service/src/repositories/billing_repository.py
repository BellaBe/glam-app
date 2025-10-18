from __future__ import annotations
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import BillingAccount, PricingProduct, Payment, PaymentStatus


class BillingAccountRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_merchant_id(self, merchant_id: str) -> BillingAccount | None:
        """Find billing account by merchant ID"""
        stmt = select(BillingAccount).where(
            BillingAccount.merchant_id == merchant_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create(
        self,
        merchant_id: str,
        platform_name: str,
        platform_shop_id: str,
        platform_domain: str,
    ) -> BillingAccount:
        """Create new billing account"""
        account = BillingAccount(
            merchant_id=merchant_id,
            platform_name=platform_name,
            platform_shop_id=platform_shop_id,
            platform_domain=platform_domain,
            trial_available=True,
            total_spend_usd=Decimal("0.00"),
        )
        self.session.add(account)
        await self.session.flush()
        await self.session.refresh(account)
        return account

    async def activate_trial(self, merchant_id: str) -> BillingAccount:
        """Activate trial for merchant"""
        account = await self.find_by_merchant_id(merchant_id)
        if not account:
            raise ValueError(f"Account not found: {merchant_id}")
        
        account.trial_available = False
        account.trial_activated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(account)
        return account

    async def update_spend(
        self,
        merchant_id: str,
        amount: Decimal,
    ) -> BillingAccount:
        """Update total spend for merchant"""
        account = await self.find_by_merchant_id(merchant_id)
        if not account:
            raise ValueError(f"Account not found: {merchant_id}")
        
        account.total_spend_usd += amount
        account.last_payment_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(account)
        return account


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, product_id: str) -> PricingProduct | None:
        """Find product by ID"""
        return await self.session.get(PricingProduct, product_id)

    async def list_active(self) -> list[PricingProduct]:
        """List all active products"""
        stmt = select(PricingProduct).where(PricingProduct.active == True)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        product_id: str,
        product_type: str,
        name: str,
        price: Decimal,
        currency: str,
        metadata: dict,
        active: bool = True,
    ) -> PricingProduct:
        """Create pricing product"""
        product = PricingProduct(
            id=product_id,
            type=product_type,
            name=name,
            price=price,
            currency=currency,
            metadata=metadata,
            active=active,
        )
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, payment_id: str) -> Payment | None:
        """Find payment by ID"""
        return await self.session.get(Payment, payment_id)

    async def find_by_platform_charge_id(
        self,
        platform_charge_id: str
    ) -> Payment | None:
        """Find payment by platform charge ID"""
        stmt = select(Payment).where(
            Payment.platform_charge_id == platform_charge_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_by_merchant(
        self,
        merchant_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Payment]:
        """List payments for merchant"""
        stmt = (
            select(Payment)
            .where(Payment.merchant_id == merchant_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        merchant_id: str,
        amount: Decimal,
        currency: str,
        description: str,
        product_type: str,
        product_id: str,
        platform_name: str,
        metadata: dict | None = None,
        expires_at: datetime | None = None,
    ) -> Payment:
        """Create payment record"""
        payment = Payment(
            merchant_id=merchant_id,
            amount=amount,
            currency=currency,
            description=description,
            product_type=product_type,
            product_id=product_id,
            status=PaymentStatus.PENDING,
            platform_name=platform_name,
            metadata=metadata,
            expires_at=expires_at,
        )
        self.session.add(payment)
        await self.session.flush()
        await self.session.refresh(payment)
        return payment

    async def update_platform_charge_id(
        self,
        payment_id: str,
        platform_charge_id: str,
    ) -> Payment:
        """Update payment with platform charge ID"""
        payment = await self.find_by_id(payment_id)
        if not payment:
            raise ValueError(f"Payment not found: {payment_id}")
        
        payment.platform_charge_id = platform_charge_id
        await self.session.flush()
        await self.session.refresh(payment)
        return payment

    async def mark_completed(self, payment_id: str) -> Payment:
        """Mark payment as completed"""
        payment = await self.find_by_id(payment_id)
        if not payment:
            raise ValueError(f"Payment not found: {payment_id}")
        
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(payment)
        return payment

    async def mark_failed(self, payment_id: str) -> Payment:
        """Mark payment as failed"""
        payment = await self.find_by_id(payment_id)
        if not payment:
            raise ValueError(f"Payment not found: {payment_id}")
        
        payment.status = PaymentStatus.FAILED
        await self.session.flush()
        await self.session.refresh(payment)
        return payment

    async def mark_refunded(self, payment_id: str) -> Payment:
        """Mark payment as refunded"""
        payment = await self.find_by_id(payment_id)
        if not payment:
            raise ValueError(f"Payment not found: {payment_id}")
        
        payment.status = PaymentStatus.REFUNDED
        payment.refunded_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(payment)
        return payment

    async def mark_expired_payments(self) -> int:
        """Mark expired pending payments"""
        from sqlalchemy import update
        
        stmt = (
            update(Payment)
            .where(
                and_(
                    Payment.status == PaymentStatus.PENDING,
                    Payment.expires_at <= datetime.now(UTC)
                )
            )
            .values(status=PaymentStatus.EXPIRED)
        )
        result = await self.session.execute(stmt)
        return result.rowcount
