# services/credit-service/src/services/credit_transaction_service.py
"""Credit transaction service - Transaction processing and audit trail."""

from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel
from shared.utils.logger import ServiceLogger
from shared.utils.idempotency_key import generate_idempotency_key
from shared.errors import DomainError, NotFoundError, ConflictError, ValidationError

from ..models.credit_transaction import CreditTransaction, TransactionType, OperationType
from ..repositories.credit_transaction_repository import CreditTransactionRepository
from ..mappers.credit_transaction_mapper import CreditTransactionMapper
from ..schemas.credit_transaction import CreditTransactionResponse, CreditTransactionListResponse, TransactionStatsByMerchantIdResponse

from ..services.credit_service import CreditService


# TODO: Move the model to a separate file/service where it belongs (probably shared)
class Trial(BaseModel):
    """Trial credits for new merchants"""
    trial_id: UUID
    merchant_id: UUID
    credits_to_use: int
    
    
class ManualAdjustment(BaseModel):
    """Manual credit adjustment by admin"""
    admin_id: str
    adjustment_id: str
    merchant_id: UUID
    operation_type: OperationType
    credits_used: int
    reason: Optional[str] = None
    
class Subscription(BaseModel):
    """Subscription renewal details"""
    id: UUID
    merchant_id: UUID
    credits_used: int


class CreditTransactionService:
    """
    Credit transaction processing service - Updates credit through credit service
    
    Transaction Types & Operations:
    - ORDER_PAID: DECREASE (customer uses credits to pay for order)
    - SUBSCRIPTION: INCREASE (subscription renewal adds credits)  
    - TRIAL: INCREASE (trial credits for new merchants)
    - MANUAL: INCREASE/DECREASE (admin adjustments or service usage)
    """
    
    def __init__(
        self,
        transaction_repo: CreditTransactionRepository,
        transaction_mapper: CreditTransactionMapper,
        credit_service: CreditService,
        logger: Optional[ServiceLogger] = None
    ):
        self.transaction_repo = transaction_repo
        self.transaction_mapper = transaction_mapper
        self.credit_service = credit_service  # Injected credit service
        self.logger = logger or ServiceLogger(__name__)

    async def process_order_paid(
        self,
        merchant_id: UUID,
        order_items: List[Dict[str, Any]],
    ) -> None:
        """Process order paid event - customer uses credits to pay for order (DECREASE)"""
        
        credit_record = await self.credit_service.get_credit(merchant_id)
            
        if not credit_record:
            raise NotFoundError(f"Credit record not found for merchant {merchant_id}")
        
        for order_item in order_items:
            order_id = order_item.get("order_id")
            order_metadata = order_item

            # Generate idempotency key
            idempotency_key = generate_idempotency_key("SHOPIFY", "ORDER", UUID(order_id))

            # Check if already processed
            existing = await self.transaction_repo.get_by_idempotency_key(idempotency_key)
            if existing:
                self.logger.info(
                    "Order already processed",
                    extra={"order_id": order_id, "merchant_id": str(merchant_id)}
                )
                continue
            
            current_balance = credit_record.balance

            # Create transaction (ORDER_PAID is DECREASE - customer uses credits)
            transaction = CreditTransaction(
                merchant_id=merchant_id,
                credit_id=credit_record.id,
                operation_type=OperationType.DECREASE,
                transaction_type=TransactionType.ORDER_PAID,
                credits_used=1,
                balance_before=current_balance,
                balance_after=current_balance - 1,
                idempotency_key=idempotency_key,
                extra_metadata={
                    **(order_metadata)
                }
            )
            
            # Save transaction first
            created_transaction = await self.transaction_repo.create_transaction(transaction)
            
            # Update credit balance through credit service
            await self.credit_service.update_balance_from_transaction(
                credit_transaction=created_transaction,
            )
            
            self.logger.info(
                "Order transaction processed",
                extra={
                    "merchant_id": str(merchant_id),
                    "order_id": order_id,
                    "transaction_id": str(created_transaction.id)
                }
            )
            
    async def process_subscription(
        self,
        subscription: Subscription
    ) -> None:
        """Process subscription renewal to create credit increase transaction"""
        
        # Generate idempotency key
        idempotency_key = generate_idempotency_key("SUBSCRIPTION", "RENEWAL", subscription.id)
        
        merchant_id = subscription.merchant_id
        
        # Check if already processed
        existing = await self.transaction_repo.get_by_idempotency_key(idempotency_key)
        if existing:
            return
        
        # Get existing credit record
        credit_record = await self.credit_service.get_credit(merchant_id)
        if not credit_record:
            raise NotFoundError(f"Credit account not found for merchant {merchant_id}")
        
        current_balance = credit_record.balance
        
        # Create transaction
        transaction = CreditTransaction(
            merchant_id=merchant_id,
            credit_id=credit_record.id,
            operation_type=OperationType.INCREASE,
            transaction_type=TransactionType.SUBSCRIPTION,
            credits_used=subscription.credits_used,
            balance_before=current_balance,
            balance_after=current_balance + subscription.credits_used,
            idempotency_key=idempotency_key,
            extra_metadata={
                **(subscription.model_dump()),
            }
        )
    
        
        # Save transaction and update balance
        created_transaction = await self.transaction_repo.create_transaction(transaction)
        
        await self.credit_service.update_balance_from_transaction(
            credit_transaction=created_transaction
        )
        
        self.logger.info(
            "Subscription transaction processed",
            extra={
                "merchant_id": str(merchant_id),
                "subscription_id": subscription.id,
                "credits_used": subscription.credits_used,
                "transaction_id": str(created_transaction.id)
            }
        )

    async def process_trial_credits(
            self,
            trial: Trial,
        ) -> None:
            """Process trial credits for new merchants"""
            
            # Generate idempotency key
            idempotency_key = generate_idempotency_key("TRIAL", "MERCHANT", trial.merchant_id)
            
            # Check if already processed
            existing = await self.transaction_repo.get_by_idempotency_key(idempotency_key)
            if existing:
                return
            
            # Get existing credit record
            credit_record = await self.credit_service.get_credit(trial.merchant_id)
            if not credit_record:
                raise NotFoundError(f"Credit record not found for merchant {trial.merchant_id}")

            current_balance = credit_record.balance
            
            # Create transaction
            transaction = CreditTransaction(
                merchant_id=trial.merchant_id,
                credit_id=credit_record.id,
                operation_type=OperationType.INCREASE,
                transaction_type=TransactionType.TRIAL,
                credits_used=trial.credits_to_use,
                balance_before=current_balance,
                balance_after=current_balance + trial.credits_to_use,
                idempotency_key=idempotency_key,
                extra_metadata={
                    **(trial.model_dump()),
                }
            )
            
            # Save transaction and update balance
            created_transaction = await self.transaction_repo.create_transaction(transaction)
            
            await self.credit_service.update_balance_from_transaction(
                credit_transaction=created_transaction
            )
            
            self.logger.info(
                "Trial credits processed",
                extra={
                    "merchant_id": str(trial.merchant_id),
                    "credit_amount": trial.credits_to_use,
                    "transaction_id": str(created_transaction.id)
                }
        )

    async def process_manual_adjustment(
        self,
        merchant_id: UUID,
        operation_type: OperationType,
        credits_to_use: int,
        reason: str,
        admin_id: str
       
    ) -> CreditTransactionResponse:
        """Process manual credit adjustment (increase or decrease)"""
        
        
        # Generate idempotency key
        idempotency_key = generate_idempotency_key("MANUAL", operation_type, UUID())
        
        # Get existing credit record
        credit_record = await self.credit_service.get_credit(merchant_id)
        if not credit_record:
            raise NotFoundError(f"Credit record not found for merchant {merchant_id}")
        
        current_balance = credit_record.balance
        
        # Calculate new balance
        if operation_type == OperationType.INCREASE:
            new_balance = current_balance + credits_to_use
        elif operation_type == OperationType.DECREASE:
            if credits_to_use > current_balance:
                raise ValidationError("Cannot decrease credits below zero")
            new_balance = current_balance - credits_to_use
        else:
            raise ValidationError(f"Invalid operation type: {operation_type}")
        
        # Create transaction
        transaction = CreditTransaction(
            merchant_id=merchant_id,
            credit_id=credit_record.id,
            operation_type=operation_type,
            transaction_type=TransactionType.MANUAL,
            credits_used=credits_to_use,
            balance_before=current_balance,
            balance_after=new_balance,
            idempotency_key=idempotency_key,
            extra_metadata={
                "reason": reason,
                "admin_id": admin_id
            }
        )
        
        # Save transaction and update balance
        created_transaction = await self.transaction_repo.create_transaction(transaction)
        
        await self.credit_service.update_balance_from_transaction(
            credit_transaction=created_transaction
        )
        
        self.logger.info(
            "Manual adjustment processed",
            extra={
                "merchant_id": str(merchant_id),
                "operation_type": operation_type.value,
                "credits_used": credits_to_use,
                "reason": reason,
                "admin_id": admin_id,
                "transaction_id": str(created_transaction.id)
            }
        )
        return self.transaction_mapper.model_to_response(created_transaction)

    async def list_transactions_by_merchant_id(
        self,
        merchant_id: UUID,
        limit: int,
        offset: int,
        operation_type: Optional[OperationType] = None,
        transaction_type: Optional[TransactionType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[int, List[CreditTransactionResponse]]:
        """List transactions with pagination and filtering"""
        
        transactions = await self.transaction_repo.get_by_merchant_id(
            merchant_id=merchant_id,
            limit=limit,
            offset=offset,
            operation_type=operation_type,
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date
        )
        
        total_count = await self.transaction_repo.count_by_merchant_id(
            merchant_id=merchant_id,
            operation_type=operation_type,
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return total_count, self.transaction_mapper.models_to_responses(transactions)

    
    async def get_transaction_by_id(self, transaction_id: UUID) -> Optional[CreditTransactionResponse]:
        """Get specific transaction by ID"""
        transaction = await self.transaction_repo.get_by_id(transaction_id)
        if not transaction:
            return None
        return self.transaction_mapper.model_to_response(transaction)

    async def get_merchant_stats(
        self,
        merchant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> TransactionStatsByMerchantIdResponse:
        """Get transaction statistics for a merchant"""
        
        stats = await self.transaction_repo.get_merchant_stats(
            merchant_id=merchant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return self.transaction_mapper.to_stats_response(merchant_id, stats)