from shared.events import DomainEventSubscriber
from shared.utils.logger import ServiceLogger
from typing import Dict, Any

class CreditEventSubscriber(DomainEventSubscriber):
    """Subscribe to credit events for usage tracking"""
    stream_name = "CREDITS"
    subject = "evt.credits.consumed"
    event_type = "evt.credits.consumed"
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
                "event_type": self.event_type,
                "correlation_id": correlation_id,
                "merchant_id": payload.get("merchant_id")
            }
        )
        
        await service.process_credit_consumption(payload, correlation_id)

class AIEventSubscriber(DomainEventSubscriber):
    """Subscribe to AI feature usage events"""
    stream_name = "AI"
    subject = "evt.ai.*"
    event_type = "evt.ai.*"
    durable_name = "analytics-ai-usage"
    
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]):
        """Process AI feature usage event"""
        service = self.get_dependency("analytics_service")
        logger = self.get_dependency("logger")
        
        payload = event["payload"]
        correlation_id = event.get("correlation_id")
        event_type = event.get("type", "")
        
        logger.info(
            "Processing AI usage event",
            extra={
                "event_type": event_type,
                "correlation_id": correlation_id,
                "merchant_id": payload.get("merchant_id")
            }
        )
        
        await service.process_ai_usage(payload, event_type, correlation_id)

class MerchantEventSubscriber(DomainEventSubscriber):
    """Subscribe to merchant lifecycle events"""
    stream_name = "MERCHANT"
    subject = "evt.merchant.*"
    event_type = "evt.merchant.*"
    durable_name = "analytics-merchant-lifecycle"
    
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]):
        """Process merchant lifecycle event"""
        service = self.get_dependency("analytics_service")
        logger = self.get_dependency("logger")
        
        payload = event["payload"]
        correlation_id = event.get("correlation_id")
        event_type = event.get("type", "")
        
        logger.info(
            "Processing merchant lifecycle event",
            extra={
                "event_type": event_type,
                "correlation_id": correlation_id,
                "merchant_id": payload.get("merchant_id")
            }
        )
        
        await service.process_merchant_lifecycle(payload, event_type, correlation_id)

class ShopifyEventSubscriber(DomainEventSubscriber):
    """Subscribe to Shopify integration events"""
    stream_name = "SHOPIFY"
    subject = "evt.shopify.*"
    event_type = "evt.shopify.*"
    durable_name = "analytics-shopify-integration"
    
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]):
        """Process Shopify integration event"""
        service = self.get_dependency("analytics_service")
        logger = self.get_dependency("logger")
        
        payload = event["payload"]
        correlation_id = event.get("correlation_id")
        event_type = event.get("type", "")
        
        logger.info(
            "Processing Shopify event",
            extra={
                "event_type": event_type,
                "correlation_id": correlation_id,
                "merchant_id": payload.get("merchant_id"),
                "shop_id": payload.get("shop_id")
            }
        )
        
        await service.process_shopify_event(payload, event_type, correlation_id)

class AuthEventSubscriber(DomainEventSubscriber):
    """Subscribe to authentication events for session tracking"""
    stream_name = "AUTH"
    subject = "evt.auth.*"
    event_type = "evt.auth.*"
    durable_name = "analytics-auth-sessions"
    
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]):
        """Process authentication event"""
        service = self.get_dependency("analytics_service")
        logger = self.get_dependency("logger")
        
        payload = event["payload"]
        correlation_id = event.get("correlation_id")
        event_type = event.get("type", "")
        
        logger.info(
            "Processing auth event",
            extra={
                "event_type": event_type,
                "correlation_id": correlation_id,
                "merchant_id": payload.get("merchant_id")
            }
        )
        
        await service.process_auth_event(payload, event_type, correlation_id)


