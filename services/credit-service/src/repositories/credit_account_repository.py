# services/credit-service/src/repositories/credit_account_repository.py
"""Repository for credit account operations."""

from typing import Optional, Dict
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.database.repository import Repository
from ..models.credit_account import CreditAccount


class CreditAccountRepository(Repository[CreditAccount]):
    """Repository for credit account operations"""
    
    def __init__(
            self, 
            model_class: type[CreditAccount],
            session_factory: async_sessionmaker[AsyncSession]
        ):
        super().__init__(model_class, session_factory)


    async def find_by_merchant_id(self, merchant_id: UUID) -> Optional[CreditAccount]:
        """Find credit account by merchant ID"""
        
        stmt = select(CreditAccount).where(CreditAccount.merchant_id == merchant_id)
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def create_credit_account(
        self,
        merchant_id: UUID,
        initial_balance: Decimal = Decimal("0.00")
    ) -> CreditAccount:
        """Create a new credit account"""
        
        account = CreditAccount(
            merchant_id=merchant_id, 
            balance=initial_balance,
            lifetime_credits=initial_balance
            )
        async with self.session_factory() as session:
            session.add(account)
            await session.commit()
            await session.refresh(account)
            
            return account
    
    async def update_balance(
        self,
        account_id: UUID,
        new_balance: Decimal,
        last_recharge_at: Optional[datetime] = None
    ) -> bool:
        """Update account balance"""
        
        update_data: Dict[str, Decimal | datetime | None] = {"balance": new_balance}

        if last_recharge_at:
            update_data["last_recharge_at"] = last_recharge_at
        
        stmt = (
            update(CreditAccount)
            .where(CreditAccount.id == account_id)
            .values(**update_data)
        )
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            await session.commit()
            return result.rowcount > 0
    
    async def increment_lifetime_credits(
        self,
        account_id: UUID,
        amount: Decimal
    ) -> bool:
        """Increment lifetime credits"""
        
        stmt = (
                update(CreditAccount)
                .where(CreditAccount.id == account_id)
                .values(lifetime_credits=CreditAccount.lifetime_credits + amount)
            )
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            await session.commit()
            
            return result.rowcount > 0
    
    async def get_merchants_with_zero_balance(self) -> list[UUID]:
        """Get all merchants with zero balance"""
        stmt = select(CreditAccount.merchant_id).where(
                CreditAccount.balance == Decimal("0.00")
            )
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return [row[0] for row in result.fetchall()]
    
    async def get_merchants_with_low_balance(self, threshold: Decimal) -> list[tuple[UUID, Decimal]]:
        """Get merchants with balance below threshold"""
        
        stmt = select(CreditAccount.merchant_id, CreditAccount.balance).where(
                CreditAccount.balance <= threshold,
                CreditAccount.balance > Decimal("0.00")
            )
        async with self.session_factory() as session:
          
            result = await session.execute(stmt)
            return [(row[0], row[1]) for row in result.fetchall()]