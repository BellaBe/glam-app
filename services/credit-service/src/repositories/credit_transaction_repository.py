# services/credit-service/src/repositories/credit_transaction_repository.py
"""Repository for credit transaction operations."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.database.repository import Repository
from shared.api.dependencies import PaginationParams
from ..models.credit_transaction import CreditTransaction, TransactionType, OperationType


class CreditTransactionRepository(Repository[CreditTransaction]):
    """Repository for credit transaction data access only"""
    
    def __init__(self, 
                model_class: type[CreditTransaction],
                session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(model_class, session_factory)
        
    async def get_by_id(self, transaction_id: UUID) -> Optional[CreditTransaction]:
        """Get transaction by ID"""
        stmt = select(CreditTransaction).where(CreditTransaction.id == transaction_id)
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[CreditTransaction]:
        """Find transaction by idempotency key"""
        stmt = select(CreditTransaction).where(
            CreditTransaction.idempotency_key == idempotency_key
        )
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_by_merchant_id(
        self,
        merchant_id: UUID,
        limit: int,
        offset: int,
        operation_type: Optional[OperationType] = None,
        transaction_type: Optional[TransactionType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CreditTransaction]:
        """Get transactions for a merchant with optional filtering"""
        
        async with self.session_factory() as session:
            stmt = select(CreditTransaction).where(
                CreditTransaction.merchant_id == merchant_id
            )
            
            # Add filters
            if operation_type:
                stmt = stmt.where(CreditTransaction.operation_type == operation_type)
            
            if transaction_type:
                stmt = stmt.where(CreditTransaction.transaction_type == transaction_type)
            
            if start_date:
                stmt = stmt.where(CreditTransaction.created_at >= start_date)
            
            if end_date:
                stmt = stmt.where(CreditTransaction.created_at <= end_date)
            
            # Order and paginate
            stmt = (
                stmt
                .order_by(desc(CreditTransaction.created_at))
                .offset(offset)
                .limit(limit)
            )
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_by_credit_id(
        self,
        credit_id: UUID,
        limit: Optional[int] = None
    ) -> List[CreditTransaction]:
        """Get recent transactions for a credit account"""
        
        stmt = (
            select(CreditTransaction)
            .where(CreditTransaction.credit_id == credit_id)
            .order_by(desc(CreditTransaction.created_at))
        )
        
        if limit:
            stmt = stmt.limit(limit)
        
        async with self.session_factory() as session:
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def count_by_merchant_id(
        self,
        merchant_id: UUID,
        operation_type: Optional[OperationType] = None,
        transaction_type: Optional[TransactionType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Count transactions for a merchant with optional filtering"""
        
        async with self.session_factory() as session:
            stmt = select(func.count(CreditTransaction.id)).where(
                CreditTransaction.merchant_id == merchant_id
            )
            
            # Add same filters as get_by_merchant_id
            if operation_type:
                stmt = stmt.where(CreditTransaction.operation_type == operation_type)
            
            if transaction_type:
                stmt = stmt.where(CreditTransaction.transaction_type == transaction_type)
            
            if start_date:
                stmt = stmt.where(CreditTransaction.created_at >= start_date)
            
            if end_date:
                stmt = stmt.where(CreditTransaction.created_at <= end_date)
            
            result = await session.execute(stmt)
            return result.scalar() or 0
    
    async def get_merchant_stats(
        self,
        merchant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """
        Get transaction statistics for a merchant.
        
        Since increases/decreases are always by 1 credit:
        - total_increases = count of increase transactions = total credits increased
        - total_decreases = count of decrease transactions = total credits decreased
        """
        
        async with self.session_factory() as session:
            # Base filters
            base_filters = [CreditTransaction.merchant_id == merchant_id]
            
            if start_date:
                base_filters.append(CreditTransaction.created_at >= start_date)
            
            if end_date:
                base_filters.append(CreditTransaction.created_at <= end_date)
            
            # Count increases (no need to sum since each is +1)
            increase_stmt = select(
                func.count(CreditTransaction.id)
            ).where(
                and_(
                    *base_filters,
                    CreditTransaction.operation_type == OperationType.INCREASE
                )
            )
            
            # Count decreases (no need to sum since each is -1)
            decrease_stmt = select(
                func.count(CreditTransaction.id)
            ).where(
                and_(
                    *base_filters,
                    CreditTransaction.operation_type == OperationType.DECREASE
                )
            )
            
            # Get latest transaction timestamp
            latest_stmt = (
                select(CreditTransaction.created_at)
                .where(and_(*base_filters))
                .order_by(desc(CreditTransaction.created_at))
                .limit(1)
            )
            
            # Execute all queries
            increase_result = await session.execute(increase_stmt)
            decrease_result = await session.execute(decrease_stmt)
            latest_result = await session.execute(latest_stmt)
            
            # Extract results
            total_increases = increase_result.scalar() or 0
            total_decreases = decrease_result.scalar() or 0
            last_transaction_at = latest_result.scalar_one_or_none()
            
            return {
                "total_increases": total_increases,          
                "total_decreases": total_decreases,         
                "transaction_count": total_increases + total_decreases,
                "last_transaction_at": last_transaction_at
            }
    
    
    async def create_transaction(
        self,
        transaction: CreditTransaction
    ) -> CreditTransaction:
        """Create a new credit transaction"""
        
        async with self.session_factory() as session:
            session.add(transaction)
            await session.commit()
            await session.refresh(transaction)
            return transaction