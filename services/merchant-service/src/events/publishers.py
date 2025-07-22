# services/merchant-service/src/events/publishers.py
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, List, Optional
from shared.events import DomainEventPublisher, Streams

class MerchantEventPublisher(DomainEventPublisher):
    """Merchant domain event publisher"""
    domain_stream = Streams.MERCHANT
    service_name_override = "merchant-service"
    
    async def publish_merchant_created(
        self,
        merchant_id: UUID,
        shop_id: str,
        shop_domain: str,
        email: str,
        platform: str,
        is_marketable: bool,
        **extra
    ):
        """Publish merchant created event"""
        await self.publish_event("evt.merchant.created", {
            "merchant_id": merchant_id,
            "shop_id": shop_id,
            "shop_domain": shop_domain,
            "email": email,
            "platform": platform,
            "is_marketable": is_marketable,
            "created_at": datetime.utcnow(),
            **extra
        })
    
    async def publish_status_changed(
        self,
        merchant_id: UUID,
        shop_id: str,
        old_status: str,
        new_status: str,
        reason: str,
        changed_by: str
    ):
        """Publish status changed event"""
        await self.publish_event("evt.merchant.status.changed", {
            "merchant_id": merchant_id,
            "shop_id": shop_id,
            "old_status": old_status,
            "new_status": new_status,
            "reason": reason,
            "changed_by": changed_by,
            "changed_at": datetime.utcnow()
        })
    
    async def publish_config_updated(
        self,
        merchant_id: UUID,
        shop_id: str,
        changed_fields: List[str],
        previous_config: Dict[str, Any],
        new_config: Dict[str, Any],
        is_marketable: bool,
        updated_by: str
    ):
        """Publish config updated event"""
        await self.publish_event("evt.merchant.config.updated", {
            "merchant_id": merchant_id,
            "shop_id": shop_id,
            "changed_fields": changed_fields,
            "previous_config": previous_config,
            "new_config": new_config,
            "is_marketable": is_marketable,
            "updated_by": updated_by,
            "updated_at": datetime.utcnow()
        })
    
    async def publish_activity_recorded(
        self,
        merchant_id: UUID,
        activity_type: str,
        activity_name: str,
        activity_description: Optional[str],
        activity_data: Dict[str, Any],
        session_id: Optional[str],
        user_agent: Optional[str],
        ip_address: Optional[str]
    ):
        """Publish activity recorded event"""
        await self.publish_event("evt.merchant.activity.recorded", {
            "merchant_id": merchant_id,
            "activity_type": activity_type,
            "activity_name": activity_name,
            "activity_description": activity_description,
            "activity_data": activity_data,
            "session_id": session_id,
            "timestamp": datetime.utcnow(),
            "user_agent": user_agent,
            "ip_address": ip_address
        })