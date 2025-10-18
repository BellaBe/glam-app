# services/credit-service/src/repositories/credit_repository.py

from __future__ import annotations
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from src.db.models import CreditAccount, CreditTransaction


class CreditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_account(self, merchant_id: UUID) -> Optional[CreditAccount]:
        """Get account without locking"""
        return await self.session.get(CreditAccount, merchant_id)

    async def get_account_for_update(self, merchant_id: UUID) -> Optional[CreditAccount]:
        """Get account with row-level lock to prevent race conditions"""
        stmt = select(CreditAccount).where(CreditAccount.merchant_id == merchant_id).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_account(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_id: str,
        platform_domain: str
    ) -> CreditAccount:
        """Create new credit account"""
        account = CreditAccount(
            merchant_id=merchant_id,
            platform_name=platform_name,
            platform_id=platform_id,
            platform_domain=platform_domain,
            trial_credits=0,
            purchased_credits=0,
            balance=0,
            total_granted=0,
            total_consumed=0,
            trial_credits_used=0
        )
        self.session.add(account)
        await self.session.flush()
        await self.session.refresh(account)
        return account

    async def transaction_exists(self, reference_type: str, reference_id: str) -> bool:
        """Check if transaction already exists (idempotency)"""
        stmt = select(CreditTransaction).where(
            CreditTransaction.reference_type == reference_type,
            CreditTransaction.reference_id == reference_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None

    async def create_transaction(
        self,
        account_id: UUID,
        merchant_id: UUID,
        amount: int,
        operation: str,
        source: str,
        balance_before: int,
        balance_after: int,
        reference_type: str,
        reference_id: str,
        trial_before: int | None = None,
        trial_after: int | None = None,
        purchased_before: int | None = None,
        purchased_after: int | None = None,
        metadata: dict | None = None
    ) -> CreditTransaction:
        """Create transaction record"""
        transaction = CreditTransaction(
            account_id=account_id,
            merchant_id=merchant_id,
            amount=amount,
            operation=operation,
            source=source,
            balance_before=balance_before,
            balance_after=balance_after,
            trial_before=trial_before,
            trial_after=trial_after,
            purchased_before=purchased_before,
            purchased_after=purchased_after,
            reference_type=reference_type,
            reference_id=reference_id,
            metadata=metadata
        )
        self.session.add(transaction)
        await self.session.flush()
        await self.session.refresh(transaction)
        return transaction
