"""Event subscribers for credit service."""

import asyncio
from typing import Dict, Any
from uuid import UUID
from decimal import Decimal

from shared.events.base_subscriber import DomainEventSubscriber
from shared.utils.logger import ServiceLogger

from ..services.credit_service import CreditService


class ShopifyOrderPaidSubscriber(DomainEventSubscriber):
    """Handle Shopify order paid events"""
    
    def __init__(
        self,
        jetstream_wrapper,
        credit_service: CreditService,
        logger: ServiceLogger
    ):
        super().__init__(
            jetstream_wrapper=jetstream_wrapper,
            domain="shopify",
            logger=logger
        )
        self.credit_service = credit_service
    
    async def handle_order_paid(self, event_data: Dict[str, Any]) -> None:
        """Handle evt.shopify.webhook.order_paid"""
        try:
            # Extract data from event
            shop_domain = event_data.get("shop_domain")
            order_id = event_data.get("order_id")
            order_total = Decimal(str(event_data.get("order_total", "0")))
            currency = event_data.get("currency", "USD")
            
            # For now, we'll need to map shop_domain to merchant_id
            # This would typically be done via a merchant lookup service
            merchant_id = UUID(event_data.get("merchant_id"))  # Assume provided
            
            await self.credit_service.process_order_paid(
                merchant_id=merchant_id,
                order_id=order_id,
                order_total=order_total,
                shop_domain=shop_domain,
                currency=currency
            )
            
            self.logger.info(
                "Processed order paid event",
                order_id=order_id,
                shop_domain=shop_domain,
                merchant_id=str(merchant_id)
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to handle order paid event",
                event_data=event_data,
                error=str(e),
                exc_info=True
            )
            raise


class ShopifyOrderRefundedSubscriber(DomainEventSubscriber):
    """Handle Shopify order refunded events"""
    
    def __init__(
        self,
        jetstream_wrapper,
        credit_service: CreditService,
        logger: ServiceLogger
    ):
        super().__init__(
            jetstream_wrapper=jetstream_wrapper,
            domain="shopify",
            logger=logger
        )
        self.credit_service = credit_service
    
    async def handle_order_refunded(self, event_data: Dict[str, Any]) -> None:
        """Handle evt.shopify.webhook.order_refunded"""
        try:
            merchant_id = UUID(event_data.get("merchant_id"))
            refund_id = event_data.get("refund_id")
            order_id = event_data.get("order_id")
            refund_amount = Decimal(str(event_data.get("refund_amount", "0")))
            reason = event_data.get("reason", "Order refunded")
            
            await self.credit_service.process_refund(
                merchant_id=merchant_id,
                refund_id=refund_id,
                original_reference_id=order_id,
                refund_amount=refund_amount,
                reason=reason
            )
            
            self.logger.info(
                "Processed order refunded event",
                refund_id=refund_id,
                order_id=order_id,
                merchant_id=str(merchant_id)
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to handle order refunded event",
                event_data=event_data,
                error=str(e),
                exc_info=True
            )
            raise


class BillingPaymentSucceededSubscriber(DomainEventSubscriber):
    """Handle billing payment events"""
    
    def __init__(
        self,
        jetstream_wrapper,
        credit_service: CreditService,
        logger: ServiceLogger
    ):
        super().__init__(
            jetstream_wrapper=jetstream_wrapper,
            domain="billing",
            logger=logger
        )
        self.credit_service = credit_service
    
    async def handle_payment_succeeded(self, event_data: Dict[str, Any]) -> None:
        """Handle evt.billing.payment_succeeded"""
        try:
            merchant_id = UUID(event_data.get("merchant_id"))
            payment_id = event_data.get("payment_id")
            amount = Decimal(str(event_data.get("amount", "0")))
            
            # Convert payment amount to credits (1:1 ratio for simplicity)
            credits = amount
            
            # Create a mock order for the billing payment
            await self.credit_service.process_order_paid(
                merchant_id=merchant_id,
                order_id=f"billing_{payment_id}",
                order_total=credits,
                shop_domain="billing.system",
                currency="USD"
            )
            
            self.logger.info(
                "Processed billing payment",
                payment_id=payment_id,
                merchant_id=str(merchant_id),
                credits=float(credits)
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to handle billing payment",
                event_data=event_data,
                error=str(e),
                exc_info=True
            )
            raise


class MerchantCreatedSubscriber(DomainEventSubscriber):
    """Handle merchant created events"""
    
    def __init__(
        self,
        jetstream_wrapper,
        credit_service: CreditService,
        logger: ServiceLogger
    ):
        super().__init__(
            jetstream_wrapper=jetstream_wrapper,
            domain="merchant",
            logger=logger
        )
        self.credit_service = credit_service
    
    async def handle_merchant_created(self, event_data: Dict[str, Any]) -> None:
        """Handle evt.merchant.created"""
        try:
            merchant_id = UUID(event_data.get("merchant_id"))
            
            # Create account with trial credits
            await self.credit_service.get_or_create_account(merchant_id)
            
            self.logger.info(
                "Created credit account for new merchant",
                merchant_id=str(merchant_id)
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to handle merchant created event",
                event_data=event_data,
                error=str(e),
                exc_info=True
            )
            raise


class ManualAdjustmentSubscriber(DomainEventSubscriber):
    """Handle manual adjustment events"""
    
    def __init__(
        self,
        jetstream_wrapper,
        credit_service: CreditService,
        logger: ServiceLogger
    ):
        super().__init__(
            jetstream_wrapper=jetstream_wrapper,
            domain="credit",
            logger=logger
        )
        self.credit_service = credit_service
    
    async def handle_manual_adjustment(self, event_data: Dict[str, Any]) -> None:
        """Handle evt.credits.manual_adjustment"""
        try:
            merchant_id = UUID(event_data.get("merchant_id"))
            adjustment_id = event_data.get("adjustment_id")
            amount = Decimal(str(event_data.get("amount", "0")))
            reason = event_data.get("reason")
            admin_id = event_data.get("admin_id")
            ticket_number = event_data.get("ticket_number")
            
            await self.credit_service.process_manual_adjustment(
                merchant_id=merchant_id,
                adjustment_id=adjustment_id,
                amount=amount,
                reason=reason,
                admin_id=admin_id,
                ticket_number=ticket_number
            )
            
            self.logger.info(
                "Processed manual adjustment",
                adjustment_id=adjustment_id,
                merchant_id=str(merchant_id),
                admin_id=admin_id
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to handle manual adjustment",
                event_data=event_data,
                error=str(e),
                exc_info=True
            )
            raise