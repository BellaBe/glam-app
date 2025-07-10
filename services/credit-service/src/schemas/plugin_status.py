# services/credit-service/src/schemas/plugin_status.py
"""Plugin status schemas."""

from decimal import Decimal
from enum import Enum
from uuid import UUID
from typing import Literal, Dict, List
from pydantic import BaseModel, Field


class PluginStatus(Enum):
    """Enum for plugin status"""
    ENABLED = "enabled"
    DISABLED = "disabled"


class PluginStatusResponse(BaseModel):
    """Plugin status response schema"""
    
    status: PluginStatus = Field(..., description="Current status of the plugin")

class PluginStatusRequest(BaseModel):
    """Plugin status check request"""
    merchant_id: UUID
    
class BatchPluginStatusRequest(BaseModel):
    """Batch plugin status check request"""
    
    merchant_ids:List[UUID] = Field(..., description="List of merchant IDs to check status for")
    
    
class BatchPluginStatusResponse(BaseModel):
    """Batch plugin status response"""
    
    statuses: Dict[UUID, PluginStatusResponse] = Field(..., description="Status by merchant ID")
    
    
class PluginStatusMetrics(BaseModel):
    """Plugin status metrics"""
    
    total_merchants: int
    enabled_count: int
    disabled_count: int
    enabled_percentage: float
    average_balance: Decimal
    zero_balance_count: int