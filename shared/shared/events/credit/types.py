# shared/events/notification/types.py
from pydantic import BaseModel, Field
from typing import Dict, List, Any
from datetime import datetime
from uuid import UUID

from ..base import EventWrapper  # Now generic
from ..context import EventContext  # Keep this!

class CreditEvents:
    "Credit command types"
    ORDER_UPDATED = "evt.order.updated" 
    ACCOUNT_CREATED = "evt.account.created"
    SUBSCRIPTION_RENEWED = "evt.subscription.renewed"
    MERCHANT_CREATED="evt.merchant.created"