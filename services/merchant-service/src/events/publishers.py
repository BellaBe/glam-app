from datetime import datetime
from typing import Optional, Dict, Any
from shared.messaging.publisher import Publisher
from shared.messaging.subjects import Subjects
from shared.api.correlation import get_correlation_context
from uuid import uuid4
from prisma.enums import MerchantStatus

class MerchantEventPublisher(Publisher):
    """Publisher for merchant domain events"""
    
    @property
    def service_name(self) -> str:
        return "merchant-service"
    
    async def publish_merchant_created(
        self,
        merchant_id: str,
        shop_gid: str,
        shop_domain: str,
        shop_name: Optional[str],
        email: Optional[str],
        timezone: str,
        currency: str,
        platform: str,
        installed_at: datetime,
        install_source: Optional[str]
    ) -> str:
        """Publish evt.merchant.created event"""
        return await self.publish_event(
            subject="evt.merchant.created.v1",
            data={
                "merchant_id": merchant_id,
                "shop_gid": shop_gid,
                "shop_domain": shop_domain,
                "shop_name": shop_name,
                "email": email,
                "timezone": timezone,
                "currency": currency,
                "platform": platform,
                "installed_at": installed_at.isoformat(),
                "install_source": install_source
            }
        )
    
    async def publish_merchant_synced(
        self,
        merchant_id: str,
        shop_gid: str,
        shop_domain: str,
        first_install: bool,
        last_auth_at: datetime,
        scopes: str
    ) -> str:
        """Publish evt.merchant.synced event"""
        return await self.publish_event(
            subject="evt.merchant.synced.v1",
            data={
                "merchant_id": merchant_id,
                "shop_gid": shop_gid,
                "shop_domain": shop_domain,
                "first_install": first_install,
                "last_auth_at": last_auth_at.isoformat(),
                "scopes": scopes
            }
        )
    
    async def publish_settings_updated(
        self,
        merchant_id: str,
        shop_gid: str,
        shop_domain: str,
        changes: Dict[str, bool],
        updated_at: datetime
    ) -> str:
        """Publish evt.merchant.settings.updated event"""
        return await self.publish_event(
            subject="evt.merchant.settings.updated.v1",
            data={
                "merchant_id": merchant_id,
                "shop_gid": shop_gid,
                "shop_domain": shop_domain,
                "changes": changes,
                "updated_at": updated_at.isoformat()
            }
        )
    
    async def publish_status_changed(
        self,
        merchant_id: str,
        shop_gid: str,
        old_status: MerchantStatus,
        new_status: MerchantStatus,
        reason: str,
        changed_at: datetime
    ) -> str:
        """Publish evt.merchant.status.changed event"""
        return await self.publish_event(
            subject="evt.merchant.status.changed.v1",
            data={
                "merchant_id": merchant_id,
                "shop_gid": shop_gid,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "reason": reason,
                "changed_at": changed_at.isoformat()
            }
        )
    
    async def publish_merchant_uninstalled(
        self,
        merchant_id: str,
        shop_gid: str,
        shop_domain: str,
        uninstalled_at: datetime,
        uninstall_reason: Optional[str]
    ) -> str:
        """Publish evt.merchant.uninstalled event"""
        return await self.publish_event(
            subject="evt.merchant.uninstalled.v1",
            data={
                "merchant_id": merchant_id,
                "shop_gid": shop_gid,
                "shop_domain": shop_domain,
                "uninstalled_at": uninstalled_at.isoformat(),
                "uninstall_reason": uninstall_reason
            }
        )
    
    async def publish_activity_recorded(
        self,
        merchant_id: str,
        shop_gid: str,
        activity_type: str,
        activity_name: str,
        activity_data: Optional[Dict[str, Any]],
        timestamp: datetime
    ) -> str:
        """Publish evt.merchant.activity.recorded event"""
        return await self.publish_event(
            subject="evt.merchant.activity.recorded.v1",
            data={
                "merchant_id": merchant_id,
                "shop_gid": shop_gid,
                "activity_type": activity_type,
                "activity_name": activity_name,
                "activity_data": activity_data,
                "timestamp": timestamp.isoformat()
            }
        )

