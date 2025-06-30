# services/notification-service/src/events/subscribers.py
from typing import Dict, Any

from shared.events.base_subscriber import DomainEventSubscriber
from shared.events.types import Commands, Events
from shared.utils.logger import ServiceLogger

from src.models.api import NotificationType
from src.services.notification_service import NotificationService

logger = ServiceLogger(__name__)


# Command Subscribers
class SendEmailCommandSubscriber(DomainEventSubscriber):
    """Handle send email commands"""
    event_type = Commands.NOTIFICATION_SEND_EMAIL
    subject = Commands.NOTIFICATION_SEND_EMAIL
    durable_name = "notification-send-email"
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Process send email command"""
        logger.info(f"Processing send email command: {event['event_id']}")
        await self.notification_service.send_email_from_event(event)


class SendBulkEmailCommandSubscriber(DomainEventSubscriber):
    """Handle send bulk email commands"""
    event_type = Commands.NOTIFICATION_SEND_BULK
    subject = Commands.NOTIFICATION_SEND_BULK
    durable_name = "notification-send-bulk"
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Process send bulk email command"""
        logger.info(f"Processing send bulk email command: {event['event_id']}")
        await self.notification_service.send_bulk_emails_from_event(event)


class UpdatePreferencesCommandSubscriber(DomainEventSubscriber):
    """Handle update preferences commands"""
    event_type = Commands.NOTIFICATION_UPDATE_PREFERENCES
    subject = Commands.NOTIFICATION_UPDATE_PREFERENCES
    durable_name = "notification-update-preferences"
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Process update preferences command"""
        logger.info(f"Processing update preferences command: {event['event_id']}")
        await self.notification_service.update_preferences_from_event(event)


# Event Subscribers (from other services)
class ShopLaunchedSubscriber(DomainEventSubscriber):
    """Handle shop launched events"""
    event_type = Events.SHOP_LAUNCHED
    subject = Events.SHOP_LAUNCHED
    durable_name = "notification-shop-launched"
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Send welcome email when shop launches"""
        logger.info(f"Processing shop launched event: {event['event_id']}")
        
        payload = event["payload"]
        await self.notification_service.send_notification(
            shop_id=payload["shop_id"],
            shop_domain=payload["shop_domain"],
            shop_email=payload["shop_email"],
            notification_type=NotificationType.WELCOME,
            template_variables={
                "shop_name": payload["shop_name"],
                "features": [
                    "Personal Style Analysis",
                    "Best Style Fit Recommendation",
                    "Proactive Tryon Analysis"
                ]
            },
            correlation_id=event.get("correlation_id"),
        )


class CatalogRegistrationCompletedSubscriber(DomainEventSubscriber):
    """Handle catalog registration completed events"""
    event_type = Events.CATALOG_PRODUCTS_REGISTERED
    subject = Events.CATALOG_PRODUCTS_REGISTERED
    durable_name = "notification-catalog-registration"
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Send registration complete email"""
        logger.info(f"Processing catalog registration completed: {event['event_id']}")
        
        payload = event["payload"]
        await self.notification_service.send_notification(
            shop_id=payload["shop_id"],
            shop_domain=payload["shop_domain"],
            shop_email=payload["shop_email"],
            notification_type=NotificationType.REGISTRATION_FINISH,
            template_variables={
                "product_count": payload["product_count"]
            },
            correlation_id=event.get("correlation_id"),
        )


class CatalogSyncCompletedSubscriber(DomainEventSubscriber):
    """Handle catalog sync completed events"""
    event_type = Events.CATALOG_SYNC_COMPLETED
    subject = Events.CATALOG_SYNC_COMPLETED
    durable_name = "notification-catalog-sync"
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Send sync notification if products were added/updated"""
        logger.info(f"Processing catalog sync completed: {event['event_id']}")
        
        payload = event["payload"]
        # Only send if there are added or updated products
        if payload.get("added_count", 0) > 0 or payload.get("updated_count", 0) > 0:
            await self.notification_service.send_notification(
                shop_id=payload["shop_id"],
                shop_domain=payload["shop_domain"],
                shop_email=payload["shop_email"],
                notification_type=NotificationType.REGISTRATION_SYNC,
                template_variables={
                    "added_count": payload.get("added_count", 0),
                    "updated_count": payload.get("updated_count", 0),
                    "removed_count": payload.get("removed_count", 0)
                },
                correlation_id=event.get("correlation_id"),
            )


class BillingSubscriptionUpdatedSubscriber(DomainEventSubscriber):
    """Handle billing subscription updated events"""
    event_type = Events.BILLING_SUBSCRIPTION_UPDATED
    subject = Events.BILLING_SUBSCRIPTION_UPDATED
    durable_name = "notification-billing-subscription"
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Handle subscription status changes"""
        logger.info(f"Processing billing subscription updated: {event['event_id']}")
        
        payload = event["payload"]
        status = payload["status"]
        previous_status = payload.get("previous_status")
        
        # Handle expired subscription
        if status in ["expired", "cancelled"] and previous_status == "active":
            await self.notification_service.send_notification(
                shop_id=payload["shop_id"],
                shop_domain=payload["shop_domain"],
                shop_email=payload["shop_email"],
                notification_type=NotificationType.BILLING_EXPIRED,
                template_variables={
                    "plan_name": payload["plan_name"],
                    "renewal_link": f"https://admin.shopify.com/store/{payload['shop_domain']}/apps/glamyouup/billing"
                },
                correlation_id=event.get("correlation_id"),
            )
            
        # Handle activated subscription
        elif status == "active" and previous_status != "active":
            await self.notification_service.send_notification(
                shop_id=payload["shop_id"],
                shop_domain=payload["shop_domain"],
                shop_email=payload["shop_email"],
                notification_type=NotificationType.BILLING_CHANGED,
                template_variables={
                    "plan_name": "Monthly Plan"
                },
                correlation_id=event.get("correlation_id"),
            )


class BillingPurchaseCompletedSubscriber(DomainEventSubscriber):
    """Handle billing purchase completed events"""
    event_type = Events.BILLING_PURCHASE_COMPLETED
    subject = Events.BILLING_PURCHASE_COMPLETED
    durable_name = "notification-billing-purchase"
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Send purchase confirmation"""
        logger.info(f"Processing billing purchase completed: {event['event_id']}")
        
        payload = event["payload"]
        await self.notification_service.send_notification(
            shop_id=payload["shop_id"],
            shop_domain=payload["shop_domain"],
            shop_email=payload["shop_email"],
            notification_type=NotificationType.BILLING_CHANGED,
            template_variables={
                "plan_name": "One Time Plan"
            },
            correlation_id=event.get("correlation_id"),
        )


class BillingBalanceLowSubscriber(DomainEventSubscriber):
    """Handle billing balance low events"""
    event_type = Events.BILLING_BALANCE_LOW
    subject = Events.BILLING_BALANCE_LOW
    durable_name = "notification-billing-low"
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Send low balance warning"""
        logger.info(f"Processing billing balance low: {event['event_id']}")
        
        payload = event["payload"]
        
        # Check frequency limit before sending
        should_send = await self.notification_service.check_frequency_limit(
            shop_id=payload["shop_id"],
            notification_type=NotificationType.BILLING_LOW_CREDITS,
            max_count=5
        )
        
        if should_send:
            await self.notification_service.send_notification(
                shop_id=payload["shop_id"],
                shop_domain=payload["shop_domain"],
                shop_email=payload["shop_email"],
                notification_type=NotificationType.BILLING_LOW_CREDITS,
                template_variables={
                    "current_balance": payload["current_balance"],
                    "days_remaining": payload["days_remaining"],
                    "expected_depletion_date": payload["expected_depletion_date"],
                    "billing_link": f"https://admin.shopify.com/store/{payload['shop_domain']}/apps/glamyouup/billing"
                },
                correlation_id=event.get("correlation_id"),
            )


class BillingBalanceZeroSubscriber(DomainEventSubscriber):
    """Handle billing balance zero events"""
    event_type = Events.BILLING_BALANCE_ZERO
    subject = Events.BILLING_BALANCE_ZERO
    durable_name = "notification-billing-zero"
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Send urgent zero balance notification"""
        logger.info(f"Processing billing balance zero: {event['event_id']}")
        
        payload = event["payload"]
        
        # Check frequency limit before sending
        should_send = await self.notification_service.check_frequency_limit(
            shop_id=payload["shop_id"],
            notification_type=NotificationType.BILLING_ZERO_BALANCE,
            max_count=2
        )
        
        if should_send:
            await self.notification_service.send_notification(
                shop_id=payload["shop_id"],
                shop_domain=payload["shop_domain"],
                shop_email=payload["shop_email"],
                notification_type=NotificationType.BILLING_ZERO_BALANCE,
                template_variables={
                    "deactivation_time": payload["deactivation_scheduled_at"],
                    "billing_link": f"https://admin.shopify.com/store/{payload['shop_domain']}/apps/glamyouup/billing"
                },
                correlation_id=event.get("correlation_id"),
            )


class BillingFeaturesDeactivatedSubscriber(DomainEventSubscriber):
    """Handle billing features deactivated events"""
    event_type = Events.BILLING_FEATURES_DEACTIVATED
    subject = Events.BILLING_FEATURES_DEACTIVATED
    durable_name = "notification-billing-deactivated"
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        
    async def on_event(self, event: Dict[str, Any], headers: Dict[str, str]) -> None:
        """Send deactivation notification"""
        logger.info(f"Processing billing features deactivated: {event['event_id']}")
        
        payload = event["payload"]
        
        # Check frequency limit before sending
        should_send = await self.notification_service.check_frequency_limit(
            shop_id=payload["shop_id"],
            notification_type=NotificationType.BILLING_DEACTIVATED,
            max_count=7
        )
        
        if should_send:
            await self.notification_service.send_notification(
                shop_id=payload["shop_id"],
                shop_domain=payload["shop_domain"],
                shop_email=payload["shop_email"],
                notification_type=NotificationType.BILLING_DEACTIVATED,
                template_variables={
                    "reason": payload["reason"],
                    "reactivation_link": f"https://admin.shopify.com/store/{payload['shop_domain']}/apps/glamyouup/billing"
                },
                correlation_id=event.get("correlation_id"),
            )