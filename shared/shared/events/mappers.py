# shared/events/mappers.py
from typing import List
from .base import Streams

# Simple service to stream mapping
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


def get_stream_subjects(stream: Streams) -> List[str]:
    """Get all subjects for a stream"""
    stream_prefix = stream.value.lower()
    return [
        f"cmd.{stream_prefix}.*",
        f"evt.{stream_prefix}.*"
    ]


def get_stream_for_service(service_name: str) -> Streams:
    """Get the stream for a service"""
    if service_name not in SERVICE_STREAM_MAP:
        raise ValueError(f"Unknown service: {service_name}")
    return SERVICE_STREAM_MAP[service_name]


def get_stream_from_event_type(event_type: str) -> Streams:
    """
    Infer stream from event type.
    Event types follow pattern: cmd.domain.* or evt.domain.*
    """
    parts = event_type.split(".")
    if len(parts) >= 2 and parts[0] in ["cmd", "evt"]:
        domain = parts[1].upper()
        if hasattr(Streams, domain):
            return Streams[domain]
    
    raise ValueError(f"Cannot infer stream from event type: {event_type}")