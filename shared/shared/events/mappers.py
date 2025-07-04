# File: shared/shared/events/mappers.py
from typing import List
from shared.events.base import EventDefinition, Streams
from shared.events.notification.types import NotificationCommands, NotificationEvents
from shared.events.catalog.types import CatalogCommands, CatalogEvents


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
    "notification-service": Streams.NOTIFICATION,
    "profile-ai-selfie": Streams.AI_PROCESSING,
    "profile-service": Streams.PROFILE,
    "rate-limit-service": Streams.RATE_LIMIT,
    "scheduler-service": Streams.SCHEDULER,
    "webhook-service": Streams.WEBHOOKS,
}


# Event Registry - Maps events to their stream configuration
EVENT_REGISTRY = {
    # Catalog Domain Commands
    # These commands are used to sync and manage catalog items
    # They can be triggered by external systems or internal processes
    
    CatalogCommands.CATALOG_SYNC_INITIAL: EventDefinition(
        stream=Streams.CATALOG,
        subjects=["cmd.catalog.*"],
        description="Initial sync catalog with external merchant system",
        payload_example={
            "merchant_id": "merchant_123",
            "source": "shopify",
            "sync_type": "full",
            "webhook_url": "https://..."
        },
        response_events=[
            CatalogEvents.CATALOG_SYNC_STARTED,
            CatalogEvents.CATALOG_SYNC_COMPLETED,
            CatalogEvents.CATALOG_SYNC_FAILED
        ]
    ),

    CatalogCommands.CATALOG_SYNC_UPDATE: EventDefinition(
        stream=Streams.CATALOG,
        subjects=["cmd.catalog.*"],
        description="Update sync catalog with external merchant system",
        payload_example={
            "merchant_id": "merchant_123",
            "items": [
                {
                    "sku": "ITEM-001",
                    "name": "Item Name",
                    "price": 99.99,
                    "images": ["url1", "url2"]
                }
            ],
            "job_id": "job_123"
        },
        response_events=[CatalogEvents.CATALOG_SYNC_COMPLETED]
    ),
    
    CatalogCommands.CATALOG_PROCESS_IMAGES: EventDefinition(
        stream=Streams.CATALOG,
        subjects=["cmd.catalog.*"],
        description="Process images for catalog items",
        payload_example={
            "merchant_id": "merchant_123",
            "items": [
                {
                    "sku": "ITEM-001",
                    "images": ["image_url_1", "image_url_2"]
                }
            ],
            "job_id": "job_123"
        },
        response_events=[
            CatalogEvents.CATALOG_IMAGES_PROCESSED,
            CatalogEvents.CATALOG_SYNC_COMPLETED
        ]
    ),
    CatalogCommands.CATALOG_ANALYZE_ITEMS: EventDefinition(
        stream=Streams.CATALOG,
        subjects=["cmd.catalog.*"],
        description="Analyze catalog items for AI enrichment",
        payload_example={
            "merchant_id": "merchant_123",
            "items": [
                {
                    "sku": "ITEM-001",
                    "name": "Item Name",
                    "description": "Item description",
                    "price": 99.99,
                    "images": ["image_url_1", "image_url_2"]
                }
            ],
            "job_id": "job_123"
        },
        response_events=[
            CatalogEvents.CATALOG_ITEMS_ANALYZED,
            CatalogEvents.CATALOG_SYNC_COMPLETED
        ]
    ),
    
    CatalogCommands.CATALOG_ENRICH_WITH_AI: EventDefinition(
        stream=Streams.CATALOG,
        subjects=["cmd.catalog.*"],
        description="Enrich catalog items with AI",
        payload_example={
            "merchant_id": "merchant_123",
            "items": [
                {
                    "sku": "ITEM-001",
                    "name": "Item Name",
                    "description": "Item description",
                    "price": 99.99,
                    "images": ["image_url_1", "image_url_2"]
                }
            ],
            "job_id": "job_123"
        },
        response_events=[
            CatalogEvents.CATALOG_AI_ENRICHED,
            CatalogEvents.CATALOG_SYNC_COMPLETED
        ]
    ),
    
    # Catalog Domain Events
    CatalogEvents.CATALOG_SYNC_COMPLETED: EventDefinition(
        stream=Streams.CATALOG,
        subjects=["evt.catalog.*"],
        description="Catalog sync completed successfully",
        payload_example={
            "job_id": "job_123",
            "merchant_id": "merchant_123",
            "summary": {
                "duration_seconds": 120,
                "items_synced": 1500,
                "items_created": 100,
                "items_updated": 1400,
                "items_removed": 50,
                "images_processed": 3000
            }
        }
    ),
    
    CatalogEvents.CATALOG_SYNC_FAILED: EventDefinition(
        stream=Streams.CATALOG,
        subjects=["evt.catalog.*"],
        description="Catalog sync failed",
        payload_example={
            "job_id": "job_123",
            "merchant_id": "merchant_123",
            "error": "Network timeout",
            "error_code": "NETWORK_TIMEOUT",
            "retry_count": 2,
            "will_retry": True,
            "failed_at": "2024-01-01T00:00:00Z"    
        }
    ),
    CatalogEvents.CATALOG_IMAGES_PROCESSED: EventDefinition(
        stream=Streams.CATALOG,
        subjects=["evt.catalog.*"],
        description="Catalog images processed successfully",
        payload_example={
            "job_id": "job_123",
            "merchant_id": "merchant_123",
            "summary": {
                "images_processed": 3000,
                "items_updated": 1500,
                "duration_seconds": 60
            }
        }
    ),
    CatalogEvents.CATALOG_ITEMS_ANALYZED: EventDefinition(
        stream=Streams.CATALOG,
        subjects=["evt.catalog.*"],
        description="Catalog items analyzed for AI enrichment",
        payload_example={
            "job_id": "job_123",
            "merchant_id": "merchant_123",
            "summary": {
                "items_analyzed": 1500,
                "duration_seconds": 90,
                "ai_enrichment_needed": 1200,
                "ai_enrichment_completed": 1000
            }
        }
    ),
    CatalogEvents.CATALOG_AI_ENRICHED: EventDefinition(
        stream=Streams.CATALOG,
        subjects=["evt.catalog.*"],
        description="Catalog items enriched with AI",
        payload_example={
            "job_id": "job_123",
            "merchant_id": "merchant_123",
            "summary": {
                "items_enriched": 1000,
                "duration_seconds": 180,
                "ai_model_used": "gpt-4",
                "enrichment_quality_score": 0.95
            }
        }
    ),
    # Notification Domain Commands
    # These commands are used to send notifications via email
    # They can be single emails or bulk emails to multiple recipients
     NotificationCommands.NOTIFICATION_SEND_EMAIL: EventDefinition(
        stream=Streams.NOTIFICATION,
        subjects=["cmd.notification.*"],
        description="Send single email notification",
        payload_example={
            "notification_type": "email",
            "recipient": {
                "shop_id": "uuid",
                "shop_domain": "example.myshopify.com",
                "email": "user@example.com",
                "dynamic_content": {
                    "order_number": "1234",
                    "customer_name": "John Doe"
                }
            },
            "metadata": {}
        },
        response_events=[
            NotificationEvents.NOTIFICATION_EMAIL_SENT,
            NotificationEvents.NOTIFICATION_EMAIL_FAILED
        ]

    ),
    
    NotificationCommands.NOTIFICATION_SEND_BULK: EventDefinition(
        stream=Streams.NOTIFICATION,
        subjects=["cmd.notification.*"],
        description="Send bulk email notifications",
        payload_example={
            "notification_type": "welcome_email",
            "recipients": [
                {
                    "shop_id": "uuid",
                    "shop_domain": "example.myshopify.com",
                    "email": "user@example.com",
                    "dynamic_content": {
                        "customer_name": "John Doe"
                    }
                },
                {
                    "shop_id": "uuid",
                    "shop_domain": "example.myshopify.com",
                    "email": "user2@example.com",
                    "dynamic_content": {
                        "customer_name": "Jane Smith"
                    }
                }
            ]
        },
        response_events=[
            NotificationEvents.NOTIFICATION_EMAIL_SENT,
            NotificationEvents.NOTIFICATION_EMAIL_FAILED,
            NotificationEvents.NOTIFICATION_BULK_SEND_COMPLETED
        ]
    ),   
    # Notification Events
    NotificationEvents.NOTIFICATION_EMAIL_SENT: EventDefinition(
        stream=Streams.NOTIFICATION,
        subjects=["evt.notification.*"],
        description="Email successfully sent",
        payload_example={
            "notification_id": "uuid",
            "shop_id": "uuid",
            "notification_type": "welcome_email",
            "provider": "sendgrid",
            "provider_message_id": "sendgrid-123",
            "sent_at": "2024-01-01T00:00:00Z"
        }
    ),

    NotificationEvents.NOTIFICATION_EMAIL_FAILED: EventDefinition(
        stream=Streams.NOTIFICATION,
        subjects=["evt.notification.*"],
        description="Notification delivery failed",
        payload_example={
            "notification_id": "uuid",
            "shop_id": "uuid",
            "notification_type": "welcome_email",
            "error": "Invalid email address",
            "error_code": "INVALID_EMAIL",
            "retry_count": 2,
            "will_retry": True,
            "failed_at": "2024-01-01T00:00:00Z"
        }
    ),
    NotificationEvents.NOTIFICATION_BULK_SEND_COMPLETED: EventDefinition(
        stream=Streams.NOTIFICATION,
        subjects=["evt.notification.*"],
        description="Bulk email send operation completed",
        payload_example={
            "notification_type": "welcome_email",
            "recipients": [
                {
                    "shop_id": "uuid",
                    "shop_domain": "example.myshopify.com",
                    "email": "john@test.com"
                }
            ]
        }
    )          
    
    #     # Auth Domain
    # Commands.AUTH_CREATE_USER: EventDefinition(
    #     stream=Streams.AUTH,
    #     subjects=["cmd.auth.*"],
    #     description="Create a new user account",
    #     payload_example={
    #         "email": "user@example.com",
    #         "password_hash": "...",
    #         "user_type": "merchant",
    #         "metadata": {}
    #     },
    #     response_events=[Events.AUTH_USER_CREATED]
    # ),
    
    # # Billing Domain
    # Events.BILLING_PAYMENT_PROCESSED: EventDefinition(
    #     stream=Streams.BILLING,
    #     subjects=["evt.billing.*"],
    #     description="Payment processed successfully",
    #     payload_example={
    #         "invoice_id": "inv_123",
    #         "merchant_id": "merchant_123",
    #         "amount": 999.99,
    #         "currency": "USD",
    #         "payment_method": "credit_card",
    #         "transaction_id": "txn_123"
    #     }
    # ),
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

