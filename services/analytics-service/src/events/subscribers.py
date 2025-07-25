from shared.events import DomainEventSubscriber
from shared.utils.logger import ServiceLogger
from typing import Dict, Any

class CreditEventSubscriber(DomainEventSubscriber):
    """Subscribe to credit events for usage tracking"""
    stream_name = "CREDITS"
    subject = "evt.credits.consumed"
    subject = "evt.credits.consumed"
    durable_name = "analytics-credit-consumed"
    
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]):
        """Process credit consumption event"""
        service = self.get_dependency("analytics_service")
        logger = self.get_dependency("logger")
        
        payload = event["payload"]
        correlation_id = event.get("correlation_id")
        
        logger.info(
            "Processing credit consumption event",
            extra={
                "subject": self.subject,
                "correlation_id": correlation_id,
                "merchant_id": payload.get("merchant_id")
            }
        )
        
        await service.process_credit_consumption(payload, correlation_id)

class AIEventSubscriber(DomainEventSubscriber):
    """Subscribe to AI feature usage events"""
    stream_name = "AI"
    subject = "evt.ai.*"
    subject = "evt.ai.*"
    durable_name = "analytics-ai-usage"
    
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]):
        """Process AI feature usage event"""
        service = self.get_dependency("analytics_service")
        logger = self.get_dependency("logger")
        
        payload = event["payload"]
        correlation_id = event.get("correlation_id")
        subject = event.get("type", "")
        
        logger.info(
            "Processing AI usage event",
            extra={
                "subject": subject,
                "correlation_id": correlation_id,
                "merchant_id": payload.get("merchant_id")
            }
        )
        
        await service.process_ai_usage(payload, subject, correlation_id)

class MerchantEventSubscriber(DomainEventSubscriber):
    """Subscribe to merchant lifecycle events"""
    stream_name = "MERCHANT"
    subject = "evt.merchant.*"
    subject = "evt.merchant.*"
    durable_name = "analytics-merchant-lifecycle"
    
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]):
        """Process merchant lifecycle event"""
        service = self.get_dependency("analytics_service")
        logger = self.get_dependency("logger")
        
        payload = event["payload"]
        correlation_id = event.get("correlation_id")
        subject = event.get("type", "")
        
        logger.info(
            "Processing merchant lifecycle event",
            extra={
                "subject": subject,
                "correlation_id": correlation_id,
                "merchant_id": payload.get("merchant_id")
            }
        )
        
        await service.process_merchant_lifecycle(payload, subject, correlation_id)

class ShopifyEventSubscriber(DomainEventSubscriber):
    """Subscribe to Shopify integration events"""
    stream_name = "SHOPIFY"
    subject = "evt.shopify.*"
    subject = "evt.shopify.*"
    durable_name = "analytics-shopify-integration"
    
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]):
        """Process Shopify integration event"""
        service = self.get_dependency("analytics_service")
        logger = self.get_dependency("logger")
        
        payload = event["payload"]
        correlation_id = event.get("correlation_id")
        subject = event.get("type", "")
        
        logger.info(
            "Processing Shopify event",
            extra={
                "subject": subject,
                "correlation_id": correlation_id,
                "merchant_id": payload.get("merchant_id"),
                "shop_id": payload.get("shop_id")
            }
        )
        
        await service.process_shopify_event(payload, subject, correlation_id)

class AuthEventSubscriber(DomainEventSubscriber):
    """Subscribe to authentication events for session tracking"""
    stream_name = "AUTH"
    subject = "evt.auth.*"
    subject = "evt.auth.*"
    durable_name = "analytics-auth-sessions"
    
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]):
        """Process authentication event"""
        service = self.get_dependency("analytics_service")
        logger = self.get_dependency("logger")
        
        payload = event["payload"]
        correlation_id = event.get("correlation_id")
        subject = event.get("type", "")
        
        logger.info(
            "Processing auth event",
            extra={
                "subject": subject,
                "correlation_id": correlation_id,
                "merchant_id": payload.get("merchant_id")
            }
        )
        
        await service.process_auth_event(payload, subject, correlation_id)


