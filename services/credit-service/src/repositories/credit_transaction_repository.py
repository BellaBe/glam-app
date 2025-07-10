# services/credit-service/src/repositories/credit_transaction_repository.py
"""Repository for credit transaction operations."""

from typing import Optional, List
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.database.repository import Repository
from shared.api.dependencies import PaginationParams
from ..models.credit_transaction import CreditTransaction, TransactionType, ReferenceType


class CreditTransactionRepository(Repository[CreditTransaction]):
    """Repository for credit transaction operations"""
    
    def __init__(self, 
                model_class: type[CreditTransaction],
                session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(model_class, session_factory)

    async def create_transaction(
        self,
        merchant_id: UUID,
        account_id: UUID,
        transaction_type: TransactionType,
        amount: Decimal,
        balance_before: Decimal,
        balance_after: Decimal,
        reference_type: ReferenceType,
        reference_id: str,
        description: str,
        idempotency_key: str,
        metadata: Optional[dict] = None
    ) -> CreditTransaction:
        """Create a new credit transaction"""
        
        transaction = CreditTransaction(
                merchant_id=merchant_id,
                account_id=account_id,
                type=transaction_type,
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after,
                reference_type=reference_type,
                reference_id=reference_id,
                description=description,
                idempotency_key=idempotency_key,
                metadata=metadata or {}
            )
        async with self.session_factory() as session:
            session.add(transaction)
            await session.commit()
            await session.refresh(transaction)
            
            return transaction
    
    async def find_by_idempotency_key(self, idempotency_key: str) -> Optional[CreditTransaction]:
        """Find transaction by idempotency key"""
        stmt = select(CreditTransaction).where(
                CreditTransaction.idempotency_key == idempotency_key
            )
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def find_by_reference(
        self,
        reference_type: ReferenceType,
        reference_id: str
    ) -> Optional[CreditTransaction]:
        """Find transaction by reference"""
        
        stmt = select(CreditTransaction).where(
                and_(
                    CreditTransaction.reference_type == reference_type,
                    CreditTransaction.reference_id == reference_id
                )
            )
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_merchant_transactions(
        self,
        merchant_id: UUID,
        pagination: PaginationParams,
        transaction_type: Optional[TransactionType] = None,
        reference_type: Optional[ReferenceType] = None
    ) -> tuple[List[CreditTransaction], int]:
        """Get paginated transactions for a merchant"""
        async with self.session_factory() as session:
            # Build base query
            base_query = select(CreditTransaction).where(
                CreditTransaction.merchant_id == merchant_id
            )
            
            # Add filters
            if transaction_type:
                base_query = base_query.where(CreditTransaction.type == transaction_type)
            
            if reference_type:
                base_query = base_query.where(CreditTransaction.reference_type == reference_type)
            
            # Count query
            count_query = select(func.count()).select_from(
                base_query.subquery()
            )
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0
            
            # Data query with pagination
            data_query = (
                base_query
                .order_by(desc(CreditTransaction.created_at))
                .offset(pagination.offset)
                .limit(pagination.limit)
            )
            
            result = await session.execute(data_query)
            transactions = list(result.scalars().all())
            
            return transactions, total
    
    async def get_account_transactions(
        self,
        account_id: UUID,
        limit: Optional[int] = None
    ) -> List[CreditTransaction]:
        """Get recent transactions for an account"""
        
        stmt = (
                select(CreditTransaction)
                .where(CreditTransaction.account_id == account_id)
                .order_by(desc(CreditTransaction.created_at))
            )
        async with self.session_factory() as session:
            if limit:
                stmt = stmt.limit(limit)
            
            result = await session.execute(stmt)
            return list(result.scalars().all())