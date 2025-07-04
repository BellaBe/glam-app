# shared/events/notification/helpers.py
from datetime import datetime, timezone
import hashlib
from typing import Dict, Optional, List, Any
from uuid import UUID

from .types import (
    Recipient, 
    SendEmailBulkCommand, 
    SendEmailBulkCommandPayload, 
    SendEmailCommand, 
    SendEmailCommandPayload
)


def create_send_email_command(
    shop_id: UUID,
    shop_domain: str,
    recipient_email: str,
    notification_type: str,
    dynamic_content: Dict[str, Any],
    idempotency_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a send email command with idempotency support.
    
    If no idempotency_key provided, generates one based on:
    - shop_id + notification_type + recipient_email + timestamp (hourly bucket)
    This prevents duplicate emails within the same hour.
    """
    if not idempotency_key:
        # Create deterministic key with hourly bucket to prevent duplicates
        hour_bucket = datetime.now(timezone.utc).strftime("%Y%m%d%H")
        key_data = f"{shop_id}:{notification_type}:{recipient_email}:{hour_bucket}"
        idempotency_key = f"send_{hashlib.sha256(key_data.encode()).hexdigest()[:16]}"
        
    recipient = Recipient(
        shop_id=shop_id,
        shop_domain=shop_domain,
        email=recipient_email,
        dynamic_content=dynamic_content
    )
    
    command = SendEmailCommand(
        idempotency_key=idempotency_key,
        data=SendEmailCommandPayload(
            notification_type=notification_type,
            recipient=recipient
        ),
        metadata=metadata or {}
    )
    
    return {
        "event_type": command.subject,
        "payload": command.data.dict(),
        "idempotency_key": idempotency_key,
        "metadata": command.metadata
    }


def create_bulk_email_command(
    notification_type: str,
    recipients: List[Dict[str, Any]],
    idempotency_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a bulk email command with idempotency support.
    
    If no idempotency_key provided, generates one based on:
    - notification_type + recipient_count + timestamp
    """
    if not idempotency_key:
        # Create unique key for this bulk operation
        timestamp = datetime.now(timezone.utc).isoformat()
        key_data = f"bulk:{notification_type}:{len(recipients)}:{timestamp}"
        idempotency_key = f"bulk_{hashlib.sha256(key_data.encode()).hexdigest()[:16]}"
    
    # Convert recipient dicts to typed objects
    typed_recipients = [
        Recipient(
            shop_id=r["shop_id"],
            shop_domain=r["shop_domain"],
            email=r["email"],
            dynamic_content=r.get("dynamic_content", {})
        )
        for r in recipients
    ]
    
    command = SendEmailBulkCommand(
        idempotency_key=idempotency_key,
        data=SendEmailBulkCommandPayload(
            notification_type=notification_type,
            recipients=typed_recipients
        ),
        metadata=metadata or {}
    )
    
    return {
        "event_type": command.subject,
        "payload": command.data.model_dump(),
        "idempotency_key": idempotency_key,
        "metadata": command.metadata
    }