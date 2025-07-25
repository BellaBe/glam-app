# shared/messaging/streams/stream_config.py

from enum import Enum
from dataclasses import dataclass
from typing import List

class Streams(str, Enum):
    """NATS JetStream streams for GLAM"""
    EVENTS = "GLAM_EVENTS"  # Single stream for MVP
    DLQ = "GLAM_DLQ"       # Dead letter queue


@dataclass
class StreamConfig:
    """Stream configuration"""
    name: str
    subjects: List[str]
    max_age_hours: int = 24
    max_msgs: int = 1000000


# MVP Stream configuration
STREAM_CONFIGS = [
    StreamConfig(
        name=Streams.EVENTS,
        subjects=["evt.*"],
        max_age_hours=24,
        max_msgs=1000000,
    ),
    StreamConfig(
        name=Streams.DLQ,
        subjects=["dlq.*"],
        max_age_hours=168,  # 7 days
        max_msgs=100000,
    )
]
