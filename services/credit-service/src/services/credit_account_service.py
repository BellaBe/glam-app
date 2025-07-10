# services/credit-service/src/services/credit_service.py
"""Core credit service business logic."""

from typing import Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone

from shared.utils.logger import ServiceLogger
from shared.errors import DomainError, NotFoundError

from ..config import ServiceConfig
from ..events.publishers import CreditEventPublisher
from ..repositories.credit_account_repository import CreditAccountRepository
from ..repositories.credit_transaction_repository import CreditTransactionRepository
from ..models.credit_transaction import TransactionType, ReferenceType, CreditTransaction
from ..mappers.credit_account_mapper import CreditAccountMapper
from ..mappers.credit_transaction_mapper import CreditTransactionMapper
from ..schemas.credit_account import CreditAccountResponse
from ..schemas.credit_transaction import CreditTransactionResponse
from ..utils.credit_calculations import calculate_order_credits
from .balance_monitor_service import BalanceMonitorService
from ..metrics import (
    increment_transaction_created,
    increment_balance_updated,
    observe_transaction_processing_time,
    set_merchant_balance_gauge,
)


class CreditService:
    """Core credit business logic"""

    def __init__(
        self,
        config: ServiceConfig,
        publisher: CreditEventPublisher,
        credit_account_repo: CreditAccountRepository,
        transaction_repo: CreditTransactionRepository,
        balance_monitor: BalanceMonitorService,
        account_mapper: CreditAccountMapper,
        transaction_mapper: CreditTransactionMapper,
        logger: ServiceLogger,
    ):
        self.config = config
        self.publisher = publisher
        self.credit_account_repo = credit_account_repo
        self.transaction_repo = transaction_repo
        self.balance_monitor = balance_monitor
        self.account_mapper = account_mapper
        self.transaction_mapper = transaction_mapper
        self.logger = logger

    async def get_or_create_account(self, merchant_id: UUID) -> CreditAccountResponse:
        """Get or create credit account for merchant"""
        account = await self.credit_account_repo.find_by_merchant_id(merchant_id)

        if not account:
            # Create account with trial credits
            account = await self.credit_account_repo.create_credit_account(
                merchant_id=merchant_id, initial_balance=self.config.TRIAL_CREDITS
            )

            # Create trial transaction
            await self._create_transaction(
                merchant_id=merchant_id,
                account_id=account.id,
                transaction_type=TransactionType.RECHARGE,
                amount=self.config.TRIAL_CREDITS,
                balance_before=Decimal("0.00"),
                balance_after=self.config.TRIAL_CREDITS,
                reference_type=ReferenceType.TRIAL,
                reference_id=str(merchant_id),
                description="Initial trial credits",
                idempotency_key=f"trial_{merchant_id}",
            )

            # Publish event
            await self.publisher.publish_credits_recharged(
                merchant_id=merchant_id,
                amount=self.config.TRIAL_CREDITS,
                new_balance=self.config.TRIAL_CREDITS,
                source="trial",
                reference_type=ReferenceType.TRIAL.value,
                reference_id=str(merchant_id),
            )

            self.logger.info(
                "Created new credit account",
                merchant_id=str(merchant_id),
                initial_balance=float(self.config.TRIAL_CREDITS),
            )

        return self.account_mapper.to_response(account)

    async def get_account(self, merchant_id: UUID) -> CreditAccountResponse:
        """Get credit account for merchant"""
        account = await self.credit_account_repo.find_by_merchant_id(merchant_id)

        if not account:
            raise NotFoundError(f"Credit account not found for merchant {merchant_id}")

        return self.account_mapper.to_response(account)

    async def process_order_paid(
        self,
        merchant_id: UUID,
        order_id: str,
        order_total: int,
        shop_domain: str,
        currency: str = "USD",
    ) -> CreditTransactionResponse:
        """Process order paid event to add credits"""
        start_time = datetime.now(timezone.utc)

        try:
            # Check idempotency
            existing = await self.transaction_repo.find_by_idempotency_key(order_id)
            if existing:
                self.logger.info(
                    "Order already processed",
                    order_id=order_id,
                    merchant_id=str(merchant_id),
                )
                return self.transaction_mapper.to_response(existing)

            # Get or create account
            account = await self.credit_account_repo.find_by_merchant_id(merchant_id)
            if not account:
                account = await self.get_or_create_account(merchant_id)

            # Calculate credits
            credits = calculate_order_credits(
                order_total=order_total,
                fixed_amount=self.config.ORDER_CREDIT_FIXED_AMOUNT,
                percentage=self.config.ORDER_CREDIT_PERCENTAGE,
                minimum=self.config.ORDER_CREDIT_MINIMUM,
            )

            old_balance = account.balance
            new_balance = old_balance + credits

            # Create transaction
            transaction = await self._create_transaction(
                merchant_id=merchant_id,
                account_id=account.id,
                transaction_type=TransactionType.RECHARGE,
                amount=credits,
                balance_before=old_balance,
                balance_after=new_balance,
                reference_type=ReferenceType.ORDER_PAID,
                reference_id=order_id,
                description=f"Credits from order {order_id}",
                idempotency_key=order_id,
                metadata={
                    "shop_domain": shop_domain,
                    "order_total": float(order_total),
                    "currency": currency,
                },
            )

            # Update account balance
            await self.credit_account_repo.update_balance(
                account_id=account.id,
                new_balance=new_balance,
                last_recharge_at=datetime.now(timezone.utc),
            )

            await self.credit_account_repo.increment_lifetime_credits(
                account_id=account.id, amount=credits
            )

            # Check balance thresholds
            await self.balance_monitor.check_balance_thresholds(
                merchant_id=merchant_id,
                old_balance=old_balance,
                new_balance=new_balance,
            )

            # Publish event
            await self.publisher.publish_credits_recharged(
                merchant_id=merchant_id,
                amount=credits,
                new_balance=new_balance,
                source="order",
                reference_type=ReferenceType.ORDER_PAID.value,
                reference_id=order_id,
            )

            # Update metrics
            increment_transaction_created(TransactionType.RECHARGE.value)
            increment_balance_updated()
            set_merchant_balance_gauge(str(merchant_id), float(new_balance))
            observe_transaction_processing_time(
                (datetime.now(timezone.utc) - start_time).total_seconds()
            )

            self.logger.info(
                "Order credits processed",
                merchant_id=str(merchant_id),
                order_id=order_id,
                credits=float(credits),
                new_balance=float(new_balance),
            )

            return self.transaction_mapper.to_response(transaction)

        except Exception as e:
            self.logger.error(
                "Failed to process order credits",
                merchant_id=str(merchant_id),
                order_id=order_id,
                error=str(e),
                exc_info=True,
            )
            raise DomainError(f"Failed to process order credits: {str(e)}")

    async def process_refund(
        self,
        merchant_id: UUID,
        refund_id: str,
        original_reference_id: str,
        refund_amount: Decimal,
        reason: str,
    ) -> CreditTransactionResponse:
        """Process refund to add credits back"""
        start_time = datetime.now(timezone.utc)

        try:
            # Check idempotency
            idempotency_key = f"refund_{refund_id}"
            existing = await self.transaction_repo.find_by_idempotency_key(
                idempotency_key
            )
            if existing:
                self.logger.info(
                    "Refund already processed",
                    refund_id=refund_id,
                    merchant_id=str(merchant_id),
                )
                return self.transaction_mapper.to_response(existing)

            # Find original transaction
            original_tx = await self.transaction_repo.find_by_reference(
                ReferenceType.ORDER_PAID, original_reference_id
            )

            if not original_tx:
                raise DomainError(
                    f"Original transaction not found: {original_reference_id}"
                )

            # Get account
            account = await self.credit_account_repo.find_by_merchant_id(merchant_id)
            if not account:
                raise NotFoundError(
                    f"Credit account not found for merchant {merchant_id}"
                )

            # Calculate refund amount (may be partial)
            actual_refund = min(refund_amount, original_tx.amount)

            old_balance = account.balance
            new_balance = old_balance + actual_refund

            # Create refund transaction
            transaction = await self._create_transaction(
                merchant_id=merchant_id,
                account_id=account.id,
                transaction_type=TransactionType.REFUND,
                amount=actual_refund,
                balance_before=old_balance,
                balance_after=new_balance,
                reference_type=ReferenceType.ORDER_REFUND,
                reference_id=refund_id,
                description=f"Refund for order {original_reference_id}",
                idempotency_key=idempotency_key,
                metadata={
                    "original_transaction_id": str(original_tx.id),
                    "reason": reason,
                },
            )

            # Update account balance
            await self.credit_account_repo.update_balance(
                account_id=account.id, new_balance=new_balance
            )

            # Check balance thresholds
            await self.balance_monitor.check_balance_thresholds(
                merchant_id=merchant_id,
                old_balance=old_balance,
                new_balance=new_balance,
            )

            # Publish event
            await self.publisher.publish_credits_refunded(
                merchant_id=merchant_id,
                amount=actual_refund,
                new_balance=new_balance,
                original_reference_id=original_reference_id,
                reason=reason,
            )

            # Update metrics
            increment_transaction_created(TransactionType.REFUND.value)
            increment_balance_updated()
            set_merchant_balance_gauge(str(merchant_id), float(new_balance))
            observe_transaction_processing_time(
                (datetime.now(timezone.utc) - start_time).total_seconds()
            )

            self.logger.info(
                "Refund processed",
                merchant_id=str(merchant_id),
                refund_id=refund_id,
                amount=float(actual_refund),
                new_balance=float(new_balance),
            )

            return self.transaction_mapper.to_response(transaction)

        except Exception as e:
            self.logger.error(
                "Failed to process refund",
                merchant_id=str(merchant_id),
                refund_id=refund_id,
                error=str(e),
                exc_info=True,
            )
            raise DomainError(f"Failed to process refund: {str(e)}")

    async def process_manual_adjustment(
        self,
        merchant_id: UUID,
        adjustment_id: str,
        amount: Decimal,
        reason: str,
        admin_id: str,
        ticket_number: Optional[str] = None,
    ) -> CreditTransactionResponse:
        """Process manual credit adjustment"""
        start_time = datetime.now(timezone.utc)

        try:
            # Validate amount
            if amount <= 0:
                raise DomainError("Adjustment amount must be positive")

            # Check idempotency
            existing = await self.transaction_repo.find_by_idempotency_key(
                adjustment_id
            )
            if existing:
                self.logger.info(
                    "Adjustment already processed",
                    adjustment_id=adjustment_id,
                    merchant_id=str(merchant_id),
                )
                return self.transaction_mapper.to_response(existing)

            # Get account
            account = await self.credit_account_repo.find_by_merchant_id(merchant_id)
            if not account:
                raise NotFoundError(
                    f"Credit account not found for merchant {merchant_id}"
                )

            old_balance = account.balance
            new_balance = old_balance + amount

            # Create adjustment transaction
            transaction = await self._create_transaction(
                merchant_id=merchant_id,
                account_id=account.id,
                transaction_type=TransactionType.ADJUSTMENT,
                amount=amount,
                balance_before=old_balance,
                balance_after=new_balance,
                reference_type=ReferenceType.MANUAL,
                reference_id=adjustment_id,
                description=reason,
                idempotency_key=adjustment_id,
                metadata={
                    "admin_id": admin_id,
                    "ticket_number": ticket_number,
                    "reason": reason,
                },
            )

            # Update account balance
            await self.credit_account_repo.update_balance(
                account_id=account.id, new_balance=new_balance
            )

            await self.credit_account_repo.increment_lifetime_credits(
                account_id=account.id, amount=amount
            )

            # Check balance thresholds
            await self.balance_monitor.check_balance_thresholds(
                merchant_id=merchant_id,
                old_balance=old_balance,
                new_balance=new_balance,
            )

            # Publish event
            await self.publisher.publish_credits_adjusted(
                merchant_id=merchant_id,
                amount=amount,
                new_balance=new_balance,
                admin_id=admin_id,
                reason=reason,
            )

            # Update metrics
            increment_transaction_created(TransactionType.ADJUSTMENT.value)
            increment_balance_updated()
            set_merchant_balance_gauge(str(merchant_id), float(new_balance))
            observe_transaction_processing_time(
                (datetime.now(timezone.utc) - start_time).total_seconds()
            )

            self.logger.info(
                "Manual adjustment processed",
                merchant_id=str(merchant_id),
                adjustment_id=adjustment_id,
                amount=float(amount),
                admin_id=admin_id,
                new_balance=float(new_balance),
            )

            return self.transaction_mapper.to_response(transaction)

        except Exception as e:
            self.logger.error(
                "Failed to process manual adjustment",
                merchant_id=str(merchant_id),
                adjustment_id=adjustment_id,
                error=str(e),
                exc_info=True,
            )
            raise DomainError(f"Failed to process manual adjustment: {str(e)}")

    async def _create_transaction(
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
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CreditTransaction:
        """Create a credit transaction"""
        return await self.transaction_repo.create_transaction(
            merchant_id=merchant_id,
            account_id=account_id,
            transaction_type=transaction_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
            idempotency_key=idempotency_key,
            metadata=metadata,
        )
