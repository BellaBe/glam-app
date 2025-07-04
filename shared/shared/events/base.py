# File: shared/shared/events/base_event.py
from pydantic import BaseModel
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from enum import Enum


class Streams(str, Enum):
    """JetStream streams organized by domain"""
    
    # Core Business Domains
    CATALOG = "CATALOG"               # Catalog management
    MERCHANT = "MERCHANT"             # Merchant management
    BILLING = "BILLING"               # Billing management
    CREDIT = "CREDIT"                 # Credit management
    
    # User & Identity
    AUTH = "AUTH"                     # Authentication & authorization
    PROFILE = "PROFILE"               # Merchant users profiles
    
    # Platform Services
    NOTIFICATION = "NOTIFICATION"   # Notification delivery
    ANALYTICS = "ANALYTICS"           # Analytics and reporting
    WEBHOOKS = "WEBHOOKS"            # Webhook delivery
    SCHEDULER = "SCHEDULER"           # Scheduled jobs
    RATE_LIMIT = "RATE_LIMIT"        # Rate limiting events
    
    # AI Services
    AI_PROCESSING = "AI_PROCESSING"   # AI/ML processing tasks



# Base event wrapper
class EventWrapper(BaseModel):
    """Base wrapper for all events with subject"""
    subject: str
    idempotency_key: Optional[str] = None
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }

@dataclass
class EventDefinition:
    """Defines an event/command with its metadata"""
    stream: Streams
    subjects: List[str]
    description: str
    payload_example: Optional[Dict] = None
    response_events: Optional[List[str]] = None  # Expected response events