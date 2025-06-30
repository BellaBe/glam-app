from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


class Streams(str, Enum):
    """JetStream streams organized by domain"""
    
    # Core Business Domains
    CATALOG = "CATALOG"               # Product catalog management
    MERCHANT = "MERCHANT"             # Merchant operations
    BILLING = "BILLING"               # Billing and payments
    CREDIT = "CREDIT"                 # Credit and financing
    
    # User & Identity
    AUTH = "AUTH"                     # Authentication & authorization
    PROFILE = "PROFILE"               # User profiles
    
    # Platform Services
    NOTIFICATIONS = "NOTIFICATIONS"   # Notification delivery
    ANALYTICS = "ANALYTICS"           # Analytics and reporting
    WEBHOOKS = "WEBHOOKS"            # Webhook delivery
    SCHEDULER = "SCHEDULER"           # Scheduled jobs
    RATE_LIMIT = "RATE_LIMIT"        # Rate limiting events
    
    # AI Services
    AI_PROCESSING = "AI_PROCESSING"   # AI/ML processing tasks


@dataclass
class EventDefinition:
    """Defines an event/command with its metadata"""
    stream: Streams
    subjects: List[str]
    description: str
    payload_example: Optional[Dict] = None
    response_events: Optional[List[str]] = None  # Expected response events


class Commands:
    """All commands in the system (cmd.*)"""
    
    # Catalog Commands
    CATALOG_SYNC = "cmd.catalog.sync"
    CATALOG_REGISTER_PRODUCTS = "cmd.catalog.register_products"
    CATALOG_UPDATE_PRODUCTS = "cmd.catalog.update_products"
    CATALOG_REMOVE_PRODUCTS = "cmd.catalog.remove_products"
    CATALOG_PROCESS_IMAGES = "cmd.catalog.process_images"
    CATALOG_ANALYZE_PRODUCTS = "cmd.catalog.analyze_products"
    CATALOG_ENRICH_WITH_AI = "cmd.catalog.enrich_with_ai"
    
    # Merchant Commands
    MERCHANT_ONBOARD = "cmd.merchant.onboard"
    MERCHANT_UPDATE_PROFILE = "cmd.merchant.update_profile"
    MERCHANT_VERIFY = "cmd.merchant.verify"
    MERCHANT_SUSPEND = "cmd.merchant.suspend"
    MERCHANT_ACTIVATE = "cmd.merchant.activate"
    
    # Billing Commands
    BILLING_CREATE_INVOICE = "cmd.billing.create_invoice"
    BILLING_PROCESS_PAYMENT = "cmd.billing.process_payment"
    BILLING_ISSUE_REFUND = "cmd.billing.issue_refund"
    BILLING_CALCULATE_COMMISSION = "cmd.billing.calculate_commission"
    
    # Credit Commands
    CREDIT_CHECK_ELIGIBILITY = "cmd.credit.check_eligibility"
    CREDIT_APPROVE_LIMIT = "cmd.credit.approve_limit"
    CREDIT_PROCESS_APPLICATION = "cmd.credit.process_application"
    CREDIT_UPDATE_SCORE = "cmd.credit.update_score"
    
    # Auth Commands
    AUTH_CREATE_USER = "cmd.auth.create_user"
    AUTH_VERIFY_EMAIL = "cmd.auth.verify_email"
    AUTH_RESET_PASSWORD = "cmd.auth.reset_password"
    AUTH_REVOKE_TOKENS = "cmd.auth.revoke_tokens"
    
    # Profile Commands
    PROFILE_CREATE = "cmd.profile.create"
    PROFILE_UPDATE = "cmd.profile.update"
    PROFILE_VERIFY_SELFIE = "cmd.profile.verify_selfie"
    PROFILE_ANALYZE_BEHAVIOR = "cmd.profile.analyze_behavior"
    
    # Notification Commands
    NOTIFICATION_SEND_EMAIL = "cmd.notification.send_email"
    NOTIFICATION_SEND_SMS = "cmd.notification.send_sms"
    NOTIFICATION_SEND_PUSH = "cmd.notification.send_push"
    NOTIFICATION_SEND_WEBHOOK = "cmd.notification.send_webhook"
    
    # Analytics Commands
    ANALYTICS_TRACK_EVENT = "cmd.analytics.track_event"
    ANALYTICS_GENERATE_REPORT = "cmd.analytics.generate_report"
    ANALYTICS_EXPORT_DATA = "cmd.analytics.export_data"
    
    # Scheduler Commands
    SCHEDULER_CREATE_JOB = "cmd.scheduler.create_job"
    SCHEDULER_CANCEL_JOB = "cmd.scheduler.cancel_job"
    SCHEDULER_UPDATE_JOB = "cmd.scheduler.update_job"
    
    # Webhook Commands
    WEBHOOK_REGISTER = "cmd.webhook.register"
    WEBHOOK_DELIVER = "cmd.webhook.deliver"
    WEBHOOK_RETRY = "cmd.webhook.retry"


class Events:
    """All events in the system (evt.*)"""
    
    # Catalog Events
    CATALOG_SYNC_STARTED = "evt.catalog.sync.started"
    CATALOG_SYNC_COMPLETED = "evt.catalog.sync.completed"
    CATALOG_SYNC_FAILED = "evt.catalog.sync.failed"
    CATALOG_PRODUCTS_REGISTERED = "evt.catalog.products.registered"
    CATALOG_PRODUCTS_UPDATED = "evt.catalog.products.updated"
    CATALOG_PRODUCTS_REMOVED = "evt.catalog.products.removed"
    CATALOG_IMAGES_PROCESSED = "evt.catalog.images.processed"
    CATALOG_IMAGES_CACHED = "evt.catalog.images.cached"
    CATALOG_AI_ANALYSIS_COMPLETED = "evt.catalog.ai_analysis.completed"
    CATALOG_ENRICHMENT_COMPLETED = "evt.catalog.enrichment.completed"
    
    # Job Events (from catalog-job-processor)
    JOB_CREATED = "evt.job.created"
    JOB_STARTED = "evt.job.started"
    JOB_PROGRESS_UPDATED = "evt.job.progress.updated"
    JOB_COMPLETED = "evt.job.completed"
    JOB_FAILED = "evt.job.failed"
    JOB_RETRY_SCHEDULED = "evt.job.retry.scheduled"
    
    # Merchant Events
    MERCHANT_ONBOARDED = "evt.merchant.onboarded"
    MERCHANT_VERIFIED = "evt.merchant.verified"
    MERCHANT_PROFILE_UPDATED = "evt.merchant.profile.updated"
    MERCHANT_SUSPENDED = "evt.merchant.suspended"
    MERCHANT_ACTIVATED = "evt.merchant.activated"
    MERCHANT_TIER_CHANGED = "evt.merchant.tier.changed"
    
    # Billing Events
    BILLING_INVOICE_CREATED = "evt.billing.invoice.created"
    BILLING_PAYMENT_PROCESSED = "evt.billing.payment.processed"
    BILLING_PAYMENT_FAILED = "evt.billing.payment.failed"
    BILLING_REFUND_ISSUED = "evt.billing.refund.issued"
    BILLING_COMMISSION_CALCULATED = "evt.billing.commission.calculated"
    BILLING_SUBSCRIPTION_UPDATED = "evt.billing.subscription.updated"
    
    # Credit Events
    CREDIT_ELIGIBILITY_CHECKED = "evt.credit.eligibility.checked"
    CREDIT_LIMIT_APPROVED = "evt.credit.limit.approved"
    CREDIT_LIMIT_REJECTED = "evt.credit.limit.rejected"
    CREDIT_APPLICATION_PROCESSED = "evt.credit.application.processed"
    CREDIT_SCORE_UPDATED = "evt.credit.score.updated"
    CREDIT_LIMIT_UTILIZED = "evt.credit.limit.utilized"
    
    # Auth Events
    AUTH_USER_CREATED = "evt.auth.user.created"
    AUTH_USER_VERIFIED = "evt.auth.user.verified"
    AUTH_PASSWORD_RESET = "evt.auth.password.reset"
    AUTH_LOGIN_SUCCESSFUL = "evt.auth.login.successful"
    AUTH_LOGIN_FAILED = "evt.auth.login.failed"
    AUTH_TOKENS_REVOKED = "evt.auth.tokens.revoked"
    
    # Profile Events
    PROFILE_CREATED = "evt.profile.created"
    PROFILE_UPDATED = "evt.profile.updated"
    PROFILE_SELFIE_VERIFIED = "evt.profile.selfie.verified"
    PROFILE_SELFIE_REJECTED = "evt.profile.selfie.rejected"
    PROFILE_BEHAVIOR_ANALYZED = "evt.profile.behavior.analyzed"
    PROFILE_RISK_SCORE_UPDATED = "evt.profile.risk_score.updated"
    
    # Notification Events
    NOTIFICATION_EMAIL_SENT = "evt.notification.email.sent"
    NOTIFICATION_SMS_SENT = "evt.notification.sms.sent"
    NOTIFICATION_PUSH_SENT = "evt.notification.push.sent"
    NOTIFICATION_DELIVERY_FAILED = "evt.notification.delivery.failed"
    NOTIFICATION_OPENED = "evt.notification.opened"
    NOTIFICATION_CLICKED = "evt.notification.clicked"
    
    # Analytics Events
    ANALYTICS_EVENT_TRACKED = "evt.analytics.event.tracked"
    ANALYTICS_REPORT_GENERATED = "evt.analytics.report.generated"
    ANALYTICS_EXPORT_COMPLETED = "evt.analytics.export.completed"
    ANALYTICS_ANOMALY_DETECTED = "evt.analytics.anomaly.detected"
    
    # Rate Limit Events
    RATE_LIMIT_EXCEEDED = "evt.rate_limit.exceeded"
    RATE_LIMIT_WARNING = "evt.rate_limit.warning"
    RATE_LIMIT_RESET = "evt.rate_limit.reset"
    
    # Webhook Events
    WEBHOOK_REGISTERED = "evt.webhook.registered"
    WEBHOOK_DELIVERED = "evt.webhook.delivered"
    WEBHOOK_DELIVERY_FAILED = "evt.webhook.delivery.failed"
    WEBHOOK_RETRY_SCHEDULED = "evt.webhook.retry.scheduled"
    
    # Scheduler Events
    SCHEDULER_JOB_CREATED = "evt.scheduler.job.created"
    SCHEDULER_JOB_EXECUTED = "evt.scheduler.job.executed"
    SCHEDULER_JOB_FAILED = "evt.scheduler.job.failed"
    SCHEDULER_JOB_CANCELLED = "evt.scheduler.job.cancelled"


# Event Registry - Maps events to their stream configuration
EVENT_REGISTRY = {
    # Catalog Domain Commands
    Commands.CATALOG_SYNC: EventDefinition(
        stream=Streams.CATALOG,
        subjects=["cmd.catalog.*"],
        description="Sync catalog with external merchant system",
        payload_example={
            "merchant_id": "merchant_123",
            "source": "shopify",
            "sync_type": "full",
            "webhook_url": "https://..."
        },
        response_events=[
            Events.CATALOG_SYNC_STARTED,
            Events.CATALOG_SYNC_COMPLETED,
            Events.CATALOG_SYNC_FAILED
        ]
    ),
    
    Commands.CATALOG_REGISTER_PRODUCTS: EventDefinition(
        stream=Streams.CATALOG,
        subjects=["cmd.catalog.*"],
        description="Register new products in catalog",
        payload_example={
            "merchant_id": "merchant_123",
            "products": [
                {
                    "sku": "PROD-001",
                    "name": "Product Name",
                    "price": 99.99,
                    "images": ["url1", "url2"]
                }
            ],
            "job_id": "job_123"
        },
        response_events=[Events.CATALOG_PRODUCTS_REGISTERED]
    ),
    
    # Catalog Domain Events
    Events.CATALOG_SYNC_COMPLETED: EventDefinition(
        stream=Streams.CATALOG,
        subjects=["evt.catalog.*"],
        description="Catalog sync completed successfully",
        payload_example={
            "job_id": "job_123",
            "merchant_id": "merchant_123",
            "summary": {
                "duration_seconds": 120,
                "products_synced": 1500,
                "products_created": 100,
                "products_updated": 1400,
                "products_removed": 50,
                "images_processed": 3000
            }
        }
    ),
    
    # Auth Domain
    Commands.AUTH_CREATE_USER: EventDefinition(
        stream=Streams.AUTH,
        subjects=["cmd.auth.*"],
        description="Create a new user account",
        payload_example={
            "email": "user@example.com",
            "password_hash": "...",
            "user_type": "merchant",
            "metadata": {}
        },
        response_events=[Events.AUTH_USER_CREATED]
    ),
    
    # Billing Domain
    Events.BILLING_PAYMENT_PROCESSED: EventDefinition(
        stream=Streams.BILLING,
        subjects=["evt.billing.*"],
        description="Payment processed successfully",
        payload_example={
            "invoice_id": "inv_123",
            "merchant_id": "merchant_123",
            "amount": 999.99,
            "currency": "USD",
            "payment_method": "credit_card",
            "transaction_id": "txn_123"
        }
    ),
    
    # Add more as needed...
}


def get_stream_config(event_type: str) -> EventDefinition:
    """Get stream configuration for an event type"""
    if event_type not in EVENT_REGISTRY:
        # For flexibility during development
        if event_type.startswith("cmd."):
            # Infer stream from command
            parts = event_type.split(".")
            if len(parts) >= 2:
                domain = parts[1].upper()
                if hasattr(Streams, domain):
                    return EventDefinition(
                        stream=Streams[domain],
                        subjects=[f"cmd.{parts[1]}.*"],
                        description="Auto-generated definition"
                    )
        elif event_type.startswith("evt."):
            # Infer stream from event
            parts = event_type.split(".")
            if len(parts) >= 2:
                domain = parts[1].upper()
                if hasattr(Streams, domain):
                    return EventDefinition(
                        stream=Streams[domain],
                        subjects=[f"evt.{parts[1]}.*"],
                        description="Auto-generated definition"
                    )
        
        raise ValueError(f"Unknown event type: {event_type}")
    
    return EVENT_REGISTRY[event_type]


def get_stream_subjects(stream: Streams) -> List[str]:
    """Get all subjects for a stream"""
    subjects = set()
    
    # Add registered subjects
    for event_def in EVENT_REGISTRY.values():
        if event_def.stream == stream:
            subjects.update(event_def.subjects)
    
    # Ensure we have basic patterns
    stream_prefix = stream.value.lower()
    subjects.add(f"cmd.{stream_prefix}.*")
    subjects.add(f"evt.{stream_prefix}.*")
    
    return list(subjects)


# Service to stream mapping for easy lookup
SERVICE_STREAM_MAP = {
    "analytics-service": Streams.ANALYTICS,
    "auth-service": Streams.AUTH,
    "billing-service": Streams.BILLING,
    "catalog-ai-service": Streams.AI_PROCESSING,
    "catalog-connector": Streams.CATALOG,
    "catalog-image-cache": Streams.CATALOG,
    "catalog-job-processor": Streams.CATALOG,
    "catalog-service": Streams.CATALOG,
    "credit-service": Streams.CREDIT,
    "merchant-service": Streams.MERCHANT,
    "notification-service": Streams.NOTIFICATIONS,
    "profile-ai-selfie": Streams.AI_PROCESSING,
    "profile-service": Streams.PROFILE,
    "rate-limit-service": Streams.RATE_LIMIT,
    "scheduler-service": Streams.SCHEDULER,
    "webhook-service": Streams.WEBHOOKS,
}