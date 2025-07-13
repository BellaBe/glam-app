# services/credit-service/src/events/subscribers.py
"""Event subscribers for internal service communication."""

from typing import Dict, Any
from uuid import UUID

from shared.events.base_subscriber import DomainEventSubscriber
from shared.utils.logger import ServiceLogger
from shared.events import EventContextManager, EventContext, EventPayload

from ..services.credit_service import CreditService
from ..services.credit_transaction_service import CreditTransactionService, Trial, Subscription

from ..models.credit_transaction import OperationType


class OrderUpdatedSubscriber(DomainEventSubscriber):
    """
    Handle transaction events to update balances.
    This creates the communication between transaction service and credit service.
    """
    
    def __init__(
        self,
        client,
        js,
        svc: CreditTransactionService,
        logger: ServiceLogger
    ):
        super().__init__(client, js, logger)
        self.credit_transaction_service = svc
        self.context_manager = EventContextManager(logger)
    
    async def handle_order_updated(self, event_data: Dict[str, Any]) -> None:
        """Handle order updated event to record credit transaction"""
        try:
            merchant_id = UUID(event_data.get("merchant_id"))
            
            await self.credit_transaction_service.process_order_paid(
                merchant_id=merchant_id,
                order_items=event_data.get("order_items", [])
            )
            
            self.logger.info("Processed order update event")
               
            
        except Exception as e:
            self.logger.error("Failed to process order update event")
            raise 

class TrialCreditsSubscriber(DomainEventSubscriber):
    """
    Handle account creation events to create trial transaction.
    """
    
    def __init__(
        self,
        client,
        js,
        svc: CreditTransactionService,
        logger: ServiceLogger
    ):
        super().__init__(client, js, logger)
        self.credit_transaction_service = svc
        self.context_manager = EventContextManager(logger)
    
    async def handle_account_created(self, event_data: Dict[str, Any]) -> None:
        """Handle account created event to create trial transaction"""
        try:
            trial_id = event_data.get("trial_id")
            merchant_id = event_data.get("merchant_id")
            credits_to_use = event_data.get("credits_to_use")
            
            trial = Trial(
                trial_id=UUID(trial_id),
                merchant_id=UUID(merchant_id),
                credits_to_use=int(str(credits_to_use))
            )
            await self.credit_transaction_service.process_trial_credits(trial=trial)
            
            self.logger.info("Trial credits transaction created")
            
        except Exception as e:
            self.logger.error("Failed to create trial credit transaction")
            raise

class SubscriptionSubscriber(DomainEventSubscriber):
    """
    Handle subscription events to create credit increase transactions.
    """
    
    def __init__(
        self,
        client,
        js,
        svc: CreditTransactionService,
        logger: ServiceLogger
    ):
        super().__init__(client, js, logger)
        self.credit_transaction_service = svc
        self.context_manager = EventContextManager(logger)
    
    async def handle_subscription_renewed(self, event_data: Dict[str, Any]) -> None:
        """Handle subscription renewal event to create credit increase transaction"""
        try:
            subscription_id = event_data.get("subscription_id")
            merchant_id = event_data.get("merchant_id")
            credits_used = event_data.get("credits_used")
            
            subscription = Subscription(
                id=UUID(subscription_id),
                merchant_id=UUID(merchant_id),
                credits_used=int(str(credits_used))
            )
            
            await self.credit_transaction_service.process_subscription(
                subscription=subscription
            )
            
            self.logger.info(
                "Processed subscription renewal event",
                extra={
                    "subscription_id": subscription_id,
                    "merchant_id": merchant_id,
                    "credits_used": credits_used
                }
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to process subscription renewal event",
                extra={
                    "event_data": event_data,
                    "error": str(e)
                }
            )
            raise

class MerchantCreatedSubscriber(DomainEventSubscriber):
    """
    Handle merchant created events to create initial credit account.
    """
    
    def __init__(
        self,
        client,
        js,
        credit_svc: CreditService,
        logger: ServiceLogger
    ):
        super().__init__(client, js, logger)
        self.credit_service = credit_svc
        self.context_manager = EventContextManager(logger)
    
    async def handle_merchant_created(self, event_data: Dict[str, Any]) -> None:
        """Handle merchant created event to create initial credit account"""
        try:
            merchant_id = event_data.get("merchant_id")
            
            # Create initial credit account for new merchant
            await self.credit_service.create_credit(
                merchant_id=UUID(merchant_id)
            )
            
            self.logger.info(
                "Processed merchant created event - credit account created",
                extra={
                    "merchant_id": merchant_id
                }
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to create credit account for new merchant",
                extra={
                    "event_data": event_data,
                    "error": str(e)
                }
            )
            raise

class ManualAdjustmentSubscriber(DomainEventSubscriber):
    """
    Handle manual adjustment events for admin credit modifications.
    """
    
    def __init__(
        self,
        client,
        js,
        svc: CreditTransactionService,
        logger: ServiceLogger
    ):
        super().__init__(client, js, logger)
        self.credit_transaction_service = svc
        self.context_manager = EventContextManager(logger)
    
    async def handle_manual_adjustment(self, event_data: Dict[str, Any]) -> None:
        """Handle manual adjustment event"""
        try:
            merchant_id = event_data.get("merchant_id")
            operation_type_str = event_data.get("operation_type")
            credits_to_use = event_data.get("credits_to_use")
            reason = event_data.get("reason", "No reason specified")
            admin_id = event_data.get("admin_id", "No admin specified")
            
            operation_type = OperationType(operation_type_str)
            
            await self.credit_transaction_service.process_manual_adjustment(
                merchant_id=UUID(merchant_id),
                operation_type=operation_type,
                credits_to_use=int(str(credits_to_use)),
                reason=reason,
                admin_id=admin_id
            )
            
            self.logger.info(
                "Processed manual adjustment event",
                extra={
                    "merchant_id": merchant_id,
                    "operation_type": operation_type,
                    "credits_to_use": credits_to_use,
                    "admin_id": admin_id
                }
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to process manual adjustment event",
                extra={
                    "event_data": event_data,
                    "error": str(e)
                }
            )
            raise