# services/notification-service/src/models/events.py
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


# Base Event Models (aligned with shared package)
class EventMetadata(BaseModel):
    """Event metadata"""
    source_service: str
    version: str = "1.0"
    user_id: Optional[UUID] = None
    trace_id: Optional[str] = None


class BaseEvent(BaseModel):
    """Base event structure"""
    event_id: UUID
    event_type: str
    correlation_id: UUID
    idempotency_key: UUID
    timestamp: datetime
    metadata: EventMetadata
    payload: Dict[str, Any]


# Command Events (Incoming)
class SendEmailCommand(BaseModel):
    """Command to send email notification"""
    class Payload(BaseModel):
        shop_id: UUID
        shop_domain: str
        type: str  # NotificationType
        to_email: str
        subject: Optional[str] = None
        template_variables: Dict[str, Any] = Field(default_factory=dict)
        metadata: Dict[str, Any] = Field(default_factory=dict)
    
    event_id: UUID
    event_type: str = "cmd.notification.send.email"
    correlation_id: UUID
    idempotency_key: UUID
    timestamp: datetime
    metadata: EventMetadata
    payload: Payload


class SendBulkEmailCommand(BaseModel):
    """Command to send bulk emails"""
    class Payload(BaseModel):
        type: str  # NotificationType
        recipients: List[Dict[str, Any]]
        subject: Optional[str] = None
        metadata: Dict[str, Any] = Field(default_factory=dict)
    
    event_id: UUID
    event_type: str = "cmd.notification.send.bulk"
    correlation_id: UUID
    idempotency_key: UUID
    timestamp: datetime
    metadata: EventMetadata
    payload: Payload


class UpdatePreferencesCommand(BaseModel):
    """Command to update notification preferences"""
    class Payload(BaseModel):
        shop_id: UUID
        shop_domain: str
        email_enabled: Optional[bool] = None
        notification_types: Optional[Dict[str, bool]] = None
        timezone: Optional[str] = None
    
    event_id: UUID
    event_type: str = "cmd.notification.update.preferences"
    correlation_id: UUID
    idempotency_key: UUID
    timestamp: datetime
    metadata: EventMetadata
    payload: Payload


# Response Events (Outgoing)
class EmailSentEvent(BaseModel):
    """Event emitted when email is sent successfully"""
    class Payload(BaseModel):
        notification_id: UUID
        shop_id: UUID
        shop_domain: str
        type: str
        to_email: str
        subject: str
        provider_message_id: str
        sent_at: datetime
    
    event_id: UUID
    event_type: str = "evt.notification.email.sent"
    correlation_id: UUID
    idempotency_key: UUID
    timestamp: datetime
    metadata: EventMetadata
    payload: Payload


class EmailFailedEvent(BaseModel):
    """Event emitted when email delivery fails"""
    class Payload(BaseModel):
        notification_id: UUID
        shop_id: UUID
        shop_domain: str
        type: str
        to_email: str
        error_code: str
        error_message: str
        retry_count: int
        will_retry: bool
    
    event_id: UUID
    event_type: str = "evt.notification.email.failed"
    correlation_id: UUID
    idempotency_key: UUID
    timestamp: datetime
    metadata: EventMetadata
    payload: Payload


class PreferencesUpdatedEvent(BaseModel):
    """Event emitted when preferences are updated"""
    class Payload(BaseModel):
        shop_id: UUID
        shop_domain: str
        email_enabled: bool
        notification_types: Dict[str, bool]
        timezone: str
        updated_at: datetime
    
    event_id: UUID
    event_type: str = "evt.notification.preferences.updated"
    correlation_id: UUID
    idempotency_key: UUID
    timestamp: datetime
    metadata: EventMetadata
    payload: Payload


# Subscription Events (from other services)
class ShopLaunchedEvent(BaseModel):
    """Event received when shop clicks launch button"""
    class Payload(BaseModel):
        shop_id: UUID
        shop_domain: str
        shop_email: str
        shop_name: str
    
    event_id: UUID
    event_type: str = "evt.shop.launched"
    correlation_id: UUID
    idempotency_key: UUID
    timestamp: datetime
    metadata: EventMetadata
    payload: Payload


class CatalogRegistrationCompletedEvent(BaseModel):
    """Event received when product registration completes"""
    class Payload(BaseModel):
        shop_id: UUID
        shop_domain: str
        shop_email: str
        product_count: int
    
    event_id: UUID
    event_type: str = "evt.catalog.registration.completed"
    correlation_id: UUID
    idempotency_key: UUID
    timestamp: datetime
    metadata: EventMetadata
    payload: Payload


class CatalogSyncCompletedEvent(BaseModel):
    """Event received when catalog sync completes"""
    class Payload(BaseModel):
        sync_id: UUID
        shop_id: UUID
        shop_domain: str
        shop_email: str
        added_count: int
        updated_count: int
        removed_count: int
    
    event_id: UUID
    event_type: str = "evt.catalog.sync.completed"
    correlation_id: UUID
    idempotency_key: UUID
    timestamp: datetime
    metadata: EventMetadata
    payload: Payload


class BillingSubscriptionUpdatedEvent(BaseModel):
    """Event received when subscription status changes"""
    class Payload(BaseModel):
        shop_id: UUID
        shop_domain: str
        shop_email: str
        subscription_id: UUID
        status: str  # active, expired, cancelled
        plan_name: str
        previous_status: Optional[str] = None
    
    event_id: UUID
    event_type: str = "evt.billing.subscription.updated"
    correlation_id: UUID
    idempotency_key: UUID
    timestamp: datetime
    metadata: EventMetadata
    payload: Payload


class BillingPurchaseCompletedEvent(BaseModel):
    """Event received when one-time purchase is completed"""
    class Payload(BaseModel):
        shop_id: UUID
        shop_domain: str
        shop_email: str
        purchase_id: UUID
        plan_name: str
        amount: float
    
    event_id: UUID
    event_type: str = "evt.billing.purchase.completed"
    correlation_id: UUID
    idempotency_key: UUID
    timestamp: datetime
    metadata: EventMetadata
    payload: Payload


class BillingBalanceLowEvent(BaseModel):
    """Event received when credit balance is low"""
    class Payload(BaseModel):
        shop_id: UUID
        shop_domain: str
        shop_email: str
        current_balance: float
        days_remaining: int
        expected_depletion_date: datetime
    
    event_id: UUID
    event_type: str = "evt.billing.balance.low"
    correlation_id: UUID
    idempotency_key: UUID
    timestamp: datetime
    metadata: EventMetadata
    payload: Payload


class BillingBalanceZeroEvent(BaseModel):
    """Event received when credit balance reaches zero"""
    class Payload(BaseModel):
        shop_id: UUID
        shop_domain: str
        shop_email: str
        deactivation_scheduled_at: datetime
    
    event_id: UUID
    event_type: str = "evt.billing.balance.zero"
    correlation_id: UUID
    idempotency_key: UUID
    timestamp: datetime
    metadata: EventMetadata
    payload: Payload


class BillingFeaturesDeactivatedEvent(BaseModel):
    """Event received when features are deactivated"""
    class Payload(BaseModel):
        shop_id: UUID
        shop_domain: str
        shop_email: str
        reason: str
    
    event_id: UUID
    event_type: str = "evt.billing.features.deactivated"
    correlation_id: UUID
    idempotency_key: UUID
    timestamp: datetime
    metadata: EventMetadata
    payload: Payload