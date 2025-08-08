from typing import Dict, Any
from datetime import datetime
from shared.messaging.listener import Listener
from shared.messaging.subjects import Subjects
from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger
from shared.api.correlation import extract_correlation_from_event
from ..schemas.billing import (
    AppSubscriptionUpdatedPayload,
    AppPurchaseUpdatedPayload,
    AppUninstalledPayload,
    SubscriptionChangedPayload,
    SubscriptionActivatedPayload,
    SubscriptionCancelledPayload,
    CreditsGrantPayload,
    SubscriptionStatus
)
from ..services.webhook_service import WebhookProcessingService
from .publishers import BillingEventPublisher

class AppSubscriptionUpdatedListener(Listener):
    """Listener for app subscription updated webhooks"""
    
    @property
    def subject(self) -> str:
        return Subjects.WEBHOOK_APP_SUBSCRIPTION_UPDATED.value
    
    @property
    def queue_group(self) -> str:
        return "billing-subscription"
    
    @property
    def service_name(self) -> str:
        return "billing-service"
    
    def __init__(
        self,
        js_client: JetStreamClient,
        webhook_service: WebhookProcessingService,
        publisher: BillingEventPublisher,
        logger: ServiceLogger,
    ):
        super().__init__(js_client, logger)
        self.webhook_service = webhook_service
        self.publisher = publisher
    
    async def on_message(self, data: dict) -> None:
        """Process subscription updated webhook"""
        correlation_id = extract_correlation_from_event(data)
        
        try:
            payload = AppSubscriptionUpdatedPayload(**data)
            
            # Process webhook
            result = await self.webhook_service.process_subscription_updated(payload)
            
            if result:
                # Publish subscription changed event
                changed_payload = SubscriptionChangedPayload(
                    shopDomain=result["shop_domain"],
                    status=result["status"],
                    planHandle=result["plan_handle"],
                    currentPeriodEnd=result["current_period_end"],
                    source="webhook",
                    correlationId=correlation_id
                )
                await self.publisher.subscription_changed(changed_payload)
                
                # Check for first activation
                if result["status"] == SubscriptionStatus.active and result["plan_handle"]:
                    activated_payload = SubscriptionActivatedPayload(
                        shopDomain=result["shop_domain"],
                        planId=result.get("plan_id", ""),
                        planHandle=result["plan_handle"],
                        correlationId=correlation_id
                    )
                    await self.publisher.subscription_activated(activated_payload)
                
                # Check for cancellation
                elif result["status"] == SubscriptionStatus.cancelled:
                    cancelled_payload = SubscriptionCancelledPayload(
                        shopDomain=result["shop_domain"],
                        correlationId=correlation_id
                    )
                    await self.publisher.subscription_cancelled(cancelled_payload)
        
        except Exception as e:
            self.logger.error(
                "Failed to process subscription webhook",
                extra={
                    "error": str(e),
                    "correlation_id": correlation_id
                },
                exc_info=True
            )
            raise

class AppPurchaseUpdatedListener(Listener):
    """Listener for app purchase updated webhooks"""
    
    @property
    def subject(self) -> str:
        return Subjects.WEBHOOK_APP_PURCHASE_UPDATED.value
    
    @property
    def queue_group(self) -> str:
        return "billing-purchase"
    
    @property
    def service_name(self) -> str:
        return "billing-service"
    
    def __init__(
        self,
        js_client: JetStreamClient,
        webhook_service: WebhookProcessingService,
        publisher: BillingEventPublisher,
        logger: ServiceLogger,
    ):
        super().__init__(js_client, logger)
        self.webhook_service = webhook_service
        self.publisher = publisher
    
    async def on_message(self, data: dict) -> None:
        """Process purchase updated webhook"""
        correlation_id = extract_correlation_from_event(data)
        
        try:
            payload = AppPurchaseUpdatedPayload(**data)
            
            # Process webhook
            result = await self.webhook_service.process_purchase_updated(payload)
            
            if result and result.get("credits"):
                # Publish credits grant event
                grant_payload = CreditsGrantPayload(
                    shopDomain=result["shop_domain"],
                    credits=result["credits"],
                    reason="one_time_pack",
                    externalRef=result["charge_id"],
                    correlationId=correlation_id
                )
                await self.publisher.credits_grant(grant_payload)
        
        except Exception as e:
            self.logger.error(
                "Failed to process purchase webhook",
                extra={
                    "error": str(e),
                    "correlation_id": correlation_id
                },
                exc_info=True
            )
            raise

class AppUninstalledListener(Listener):
    """Listener for app uninstalled webhooks"""
    
    @property
    def subject(self) -> str:
        return Subjects.WEBHOOK_APP_UNINSTALLED.value
    
    @property
    def queue_group(self) -> str:
        return "billing-uninstall"
    
    @property
    def service_name(self) -> str:
        return "billing-service"
    
    def __init__(
        self,
        js_client: JetStreamClient,
        webhook_service: WebhookProcessingService,
        publisher: BillingEventPublisher,
        logger: ServiceLogger,
    ):
        super().__init__(js_client, logger)
        self.webhook_service = webhook_service
        self.publisher = publisher
    
    async def on_message(self, data: dict) -> None:
        """Process app uninstalled webhook"""
        correlation_id = extract_correlation_from_event(data)
        
        try:
            payload = AppUninstalledPayload(**data)
            
            # Process webhook
            await self.webhook_service.process_app_uninstalled(payload)
            
            # Publish subscription cancelled event
            cancelled_payload = SubscriptionCancelledPayload(
                shopDomain=payload.shop_domain,
                reason="app_uninstalled",
                correlationId=correlation_id
            )
            await self.publisher.subscription_cancelled(cancelled_payload)
        
        except Exception as e:
            self.logger.error(
                "Failed to process uninstall webhook",
                extra={
                    "error": str(e),
                    "correlation_id": correlation_id
                },
                exc_info=True
            )
            raise

