# services/credit-service/src/repositories/credit_repository.py
"""Repository for credit account operations."""

from typing import Optional, Dict
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.database.repository import Repository
from ..models.credit import Credit


class CreditRepository(Repository[Credit]):
    """Repository for credit account operations"""

    def __init__(
        self,
        model_class: type[Credit],
        session_factory: async_sessionmaker[AsyncSession],
    ):
        super().__init__(model_class, session_factory)

    async def find_by_merchant_id(self, merchant_id: UUID) -> Optional[Credit]:
        """Find credit account by merchant ID"""

        stmt = select(Credit).where(Credit.merchant_id == merchant_id)
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def create_credit(
        self, merchant_id: UUID, initial_balance: int = 0
    ) -> Credit:
        """Create a new credit account"""

        account = Credit(
            merchant_id=merchant_id,
            balance=initial_balance,
        )
        async with self.session_factory() as session:
            session.add(account)
            await session.commit()
            await session.refresh(account)

            return account

    async def update_balance(
        self,
        credit_record_id: UUID,
        new_balance: int,
        transaction_id: UUID
    ) -> bool:
        """Update account balance"""

        update_data: Dict[str, int |UUID] = {"balance": new_balance, "last_transaction_id": transaction_id}

        stmt = update(Credit).where(Credit.id == credit_record_id).values(**update_data)
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0

    async def get_merchants_with_zero_balance(self) -> list[Credit]:
        """Get all merchants with zero balance"""
        stmt = select(Credit).where(Credit.balance == 0)
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return list(result.scalars().all())

            

    async def get_merchants_with_low_balance(
        self, threshold: int
    ) -> list[tuple[UUID, int]]:
        """Get merchants with balance below threshold"""

        stmt = select(Credit.merchant_id, Credit.balance).where(
            Credit.balance <= threshold, Credit.balance > 0
        )
        async with self.session_factory() as session:

            result = await session.execute(stmt)
            return [(row[0], row[1]) for row in result.fetchall()]
