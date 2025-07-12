# services/credit-service/src/services/credit_service.py
"""Core credit service - Account state management only."""

from uuid import UUID
from typing import List

from shared.utils.logger import ServiceLogger
from shared.errors import NotFoundError, DomainError

from ..config import CreditServiceConfig
from ..events.publishers import CreditEventPublisher
from ..repositories.credit_repository import CreditRepository
from ..mappers.credit_mapper import CreditMapper
from ..schemas.credit import CreditResponse
from ..models.credit_transaction import CreditTransaction, OperationType
from .balance_monitor_service import BalanceMonitorService
from ..metrics import (
    increment_balance_updated,
    set_merchant_balance_gauge,
)


class CreditService:
    """Credits state management service - NO transaction processing"""
    
    def __init__(
        self,
        config: CreditServiceConfig,
        credit_repo: CreditRepository,
        publisher: CreditEventPublisher,
        balance_monitor: BalanceMonitorService,
        credit_mapper: CreditMapper,
        logger: ServiceLogger
    ):
        self.config = config
        self.publisher = publisher
        self.credit_repo = credit_repo
        self.balance_monitor = balance_monitor
        self.credit_mapper = credit_mapper
        self.logger = logger
    
    async def create_credit(self, merchant_id: UUID) -> CreditResponse:
        """Create a new credit record for merchant"""
        existing_credit = await self.credit_repo.find_by_merchant_id(merchant_id)
        
        if existing_credit:
            raise DomainError(f"Credit record already exists for merchant {merchant_id}")

        credit = await self.credit_repo.create_credit(
            merchant_id=merchant_id,
            initial_balance=self.config.TRIAL_CREDITS
        )

        # Publish account created event
        await self.publisher.publish_credit_record_created(
            merchant_id=merchant_id,
            initial_balance=self.config.TRIAL_CREDITS
        )

        self.logger.info(
            "Created new credit account",
            merchant_id=str(merchant_id),
            initial_balance=float(self.config.TRIAL_CREDITS)
        )

        return self.credit_mapper.model_to_response(credit)

    async def get_credit(self, merchant_id: UUID) -> CreditResponse:
        """Get credit account for merchant"""
        credit = await self.credit_repo.find_by_merchant_id(merchant_id)
        
        if not credit:
            raise NotFoundError(f"Credit account not found for merchant {merchant_id}")
        
        return self.credit_mapper.model_to_response(credit)

    async def update_balance_from_transaction(
        self,
        credit_transaction: CreditTransaction
    ) -> None:
        """
        Update balance based on transaction event.
        This is called by transaction service via events.
        """
        credit_record = await self.credit_repo.find_by_merchant_id(credit_transaction.merchant_id)
        if not credit_record:
            raise NotFoundError(f"Credit account not found for merchant {credit_transaction.merchant_id}")

        old_balance = credit_record.balance
        
        if credit_transaction.operation_type == OperationType.INCREASE:
            new_balance: int = old_balance + 1
        else:
            new_balance: int = old_balance - 1

        # Update balance and last transaction timestamp
        await self.credit_repo.update_balance(
            credit_record_id=credit_record.id,
            new_balance=new_balance,
            transaction_id=credit_transaction.id
        )


        # Check balance thresholds
        await self.balance_monitor.check_balance_thresholds(
            merchant_id=credit_transaction.merchant_id,
            old_balance=old_balance,
            new_balance=new_balance,
        )

        # Update metrics
        increment_balance_updated()
        set_merchant_balance_gauge(str(credit_transaction.merchant_id), float(new_balance))

        # Get updated credit
        await self.credit_repo.find_by_merchant_id(credit_transaction.merchant_id)

        self.logger.info(
            "Balance updated from transaction",
            merchant_id=str(credit_transaction.merchant_id),
            old_balance=float(old_balance),
            new_balance=float(new_balance),
            transaction_id=credit_transaction.id,
            transaction_type=credit_transaction.transaction_type
        )
        
    async def get_merchants_with_zero_balance(self) -> List[CreditResponse]:
        """Get all merchant with zero balance"""
        
        credits = await self.credit_repo.get_merchants_with_zero_balance()
        
        items = self.credit_mapper.models_to_responses(credits)

        return items
