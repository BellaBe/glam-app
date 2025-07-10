# shared/events/notification/helpers.py
from datetime import datetime, timezone
import hashlib
from typing import Dict, Optional, List, Any
from uuid import UUID

from ..context import EventContext
from .types import (
    Recipient,
    SendEmailBulkCommand,
    SendEmailCommand,
)


def create_send_email_command(
    merchant_id: UUID,
    shop_domain: str,
    recipient_email: str,
    notification_type: str,
    dynamic_content: Dict[str, Any],
    unsubscribe_token: str,
    idempotency_key: Optional[str] = None,
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a send email command with idempotency support and context.

    If no idempotency_key provided, generates one based on:
    - merchant_id + notification_type + recipient_email + timestamp (hourly bucket)
    This prevents duplicate emails within the same hour.
    """
    if not idempotency_key:
        # Create deterministic key with hourly bucket to prevent duplicates
        hour_bucket = datetime.now(timezone.utc).strftime("%Y%m%d%H")
        key_data = f"{merchant_id}:{notification_type}:{recipient_email}:{hour_bucket}"
        idempotency_key = f"send_{hashlib.sha256(key_data.encode()).hexdigest()[:16]}"

    # Create event context
    context = EventContext.create(
        event_type="cmd.notification.send_email",
        source_service=(
            metadata.get("source_service", "unknown") if metadata else "unknown"
        ),
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        metadata=metadata,
    )

    recipient = Recipient(
        merchant_id=merchant_id,
        shop_domain=shop_domain,
        email=recipient_email,
        unsubscribe_token=unsubscribe_token,
        dynamic_content=dynamic_content,
    )

    command = SendEmailCommand.create_from_context(
        context=context, notification_type=notification_type, recipient=recipient
    )

    return command.to_event_dict()


def create_bulk_email_command(
    notification_type: str,
    recipients: List[Dict[str, Any]],
    idempotency_key: Optional[str] = None,
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a bulk email command with idempotency support and context.

    If no idempotency_key provided, generates one based on:
    - notification_type + recipient_count + timestamp
    """
    if not idempotency_key:
        # Create unique key for this bulk operation
        timestamp = datetime.now(timezone.utc).isoformat()
        key_data = f"bulk:{notification_type}:{len(recipients)}:{timestamp}"
        idempotency_key = f"bulk_{hashlib.sha256(key_data.encode()).hexdigest()[:16]}"

    # Create event context
    context = EventContext.create(
        event_type="cmd.notification.bulk_send",
        source_service=(
            metadata.get("source_service", "unknown") if metadata else "unknown"
        ),
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        metadata=metadata,
    )

    # Convert recipient dicts to typed objects
    typed_recipients = [
        Recipient(
            merchant_id=r["merchant_id"],
            shop_domain=r["shop_domain"],
            email=r["email"],
            unsubscribe_token=r["unsubscribe_token"],
            dynamic_content=r.get("dynamic_content", {}),
        )
        for r in recipients
    ]

    command = SendEmailBulkCommand.create_from_context(
        context=context,
        notification_type=notification_type,
        recipients=typed_recipients,
    )

    return command.to_event_dict()
