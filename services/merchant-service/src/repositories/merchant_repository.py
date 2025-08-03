from typing import Optional, List
from uuid import UUID
from datetime import datetime
from prisma import Prisma
from prisma.models import Merchant, MerchantSettings, MerchantConsent, IdempotencyKey
from prisma.enums import MerchantStatus, ConsentType
from ..schemas.merchant import MerchantSync, MerchantSettingsUpdate

class MerchantRepository:
    """Repository for Merchant operations using Prisma"""
    
    def __init__(self, prisma: Prisma):
        self.prisma = prisma
    
    async def find_by_domain(self, shop_domain: str) -> Optional[Merchant]:
        """Find merchant by shop domain"""
        return await self.prisma.merchant.find_unique(
            where={"shop_domain": shop_domain.lower()}
        )
    
    async def find_by_gid(self, shop_gid: str) -> Optional[Merchant]:
        """Find merchant by shop GID"""
        return await self.prisma.merchant.find_unique(
            where={"shop_gid": shop_gid}
        )
    
    async def find_by_domain_or_gid(self, shop_domain: str, shop_gid: str) -> Optional[Merchant]:
        """Find merchant by domain or GID"""
        merchant = await self.prisma.merchant.find_first(
            where={
                "OR": [
                    {"shop_domain": shop_domain.lower()},
                    {"shop_gid": shop_gid}
                ]
            }
        )
        return merchant
    
    async def create(self, data: MerchantSync) -> Merchant:
        """Create new merchant"""
        merchant = await self.prisma.merchant.create(
            data={
                "shop_domain": data.shop_domain.lower(),
                "shop_gid": data.shop_gid,
                "shop_name": data.shop_name,
                "email": data.email,
                "timezone": data.timezone or "UTC",
                "currency": data.currency or "USD",
                "platform": "shopify",
                "platform_api_version": data.platform_api_version or "2024-01",
                "installed_at": datetime.utcnow(),
                "last_auth_at": data.auth_at,
                "app_version": data.app_version,
                "scopes": data.scopes,
                "install_source": data.install_source or "app_store",
                "status": MerchantStatus.PENDING
            }
        )
        
        # Create default settings
        await self.prisma.merchantsettings.create(
            data={
                "merchant_id": merchant.id,
                "data_access": False,
                "auto_sync": False,
                "tos": False
            }
        )
        
        return merchant
    
    async def update(self, merchant_id: str, data: dict) -> Merchant:
        """Update merchant"""
        return await self.prisma.merchant.update(
            where={"id": merchant_id},
            data=data
        )
    
    async def update_for_reinstall(self, merchant_id: str, data: MerchantSync) -> Merchant:
        """Update merchant for reinstall"""
        return await self.prisma.merchant.update(
            where={"id": merchant_id},
            data={
                "uninstalled_at": None,
                "last_auth_at": data.auth_at,
                "app_version": data.app_version,
                "scopes": data.scopes,
                "shop_name": data.shop_name,
                "email": data.email,
                "timezone": data.timezone or "UTC",
                "currency": data.currency or "USD",
                "platform_api_version": data.platform_api_version or "2024-01",
                "install_source": data.install_source
            }
        )
    
    async def update_status(self, merchant_id: str, new_status: MerchantStatus, reason: str, previous_status: MerchantStatus) -> Merchant:
        """Update merchant status"""
        return await self.prisma.merchant.update(
            where={"id": merchant_id},
            data={
                "status": new_status,
                "previous_status": previous_status,
                "status_reason": reason,
                "status_changed_at": datetime.utcnow()
            }
        )
    
    async def update_last_activity(self, merchant_id: str) -> None:
        """Update last activity timestamp"""
        await self.prisma.merchant.update(
            where={"id": merchant_id},
            data={"last_activity_at": datetime.utcnow()}
        )
    
    async def mark_uninstalled(self, merchant_id: str, reason: Optional[str] = None) -> Merchant:
        """Mark merchant as uninstalled"""
        return await self.prisma.merchant.update(
            where={"id": merchant_id},
            data={
                "uninstalled_at": datetime.utcnow(),
                "uninstall_reason": reason
            }
        )
    
    # Settings operations
    async def get_settings(self, merchant_id: str) -> Optional[MerchantSettings]:
        """Get merchant settings"""
        return await self.prisma.merchantsettings.find_unique(
            where={"merchant_id": merchant_id}
        )
    
    async def update_settings(self, merchant_id: str, updates: MerchantSettingsUpdate) -> MerchantSettings:
        """Update merchant settings"""
        update_data = {k: v for k, v in updates.model_dump(exclude_unset=True).items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        update_data["updated_by"] = "merchant-ui"
        
        return await self.prisma.merchantsettings.update(
            where={"merchant_id": merchant_id},
            data=update_data
        )
    
    # Consent operations
    async def create_consent_audit(self, merchant_id: str, consent_type: ConsentType, accepted: bool, source: str, ip: Optional[str] = None, user_agent: Optional[str] = None) -> MerchantConsent:
        """Create consent audit record"""
        return await self.prisma.merchantconsent.create(
            data={
                "merchant_id": merchant_id,
                "type": consent_type,
                "accepted": accepted,
                "source": source,
                "ip": ip,
                "user_agent": user_agent,
                "occurred_at": datetime.utcnow()
            }
        )
    
    # Idempotency operations
    async def check_idempotency_key(self, key: str) -> bool:
        """Check if idempotency key exists"""
        result = await self.prisma.idempotencykey.find_unique(
            where={"key": key}
        )
        return result is not None
    
    async def create_idempotency_key(self, key: str, scope: str) -> None:
        """Create idempotency key"""
        await self.prisma.idempotencykey.create(
            data={
                "key": key,
                "scope": scope
            }
        )

