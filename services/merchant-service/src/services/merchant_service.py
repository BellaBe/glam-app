from uuid import UUID
from typing import Optional, Dict, Tuple
from datetime import datetime
from shared.utils.logger import ServiceLogger
from shared.api.correlation import get_correlation_context
from ..repositories.merchant_repository import MerchantRepository
from ..schemas.merchant import (
    MerchantSync, MerchantOut, MerchantSettingsUpdate, 
    MerchantSettingsOut, MerchantSyncOut, MerchantActivity
)
from ..events.publishers import MerchantEventPublisher
from ..exceptions import (
    MerchantNotFoundError, InvalidDomainError, 
    InvalidStatusTransitionError, ConsentViolationError
)
from prisma.enums import MerchantStatus, ConsentType
import redis.asyncio as redis

# Status transition rules
STATUS_TRANSITIONS = {
    MerchantStatus.PENDING: [MerchantStatus.ACTIVE, MerchantStatus.DEACTIVATED],
    MerchantStatus.ACTIVE: [MerchantStatus.SUSPENDED, MerchantStatus.DEACTIVATED],
    MerchantStatus.SUSPENDED: [MerchantStatus.ACTIVE, MerchantStatus.DEACTIVATED],
    MerchantStatus.DEACTIVATED: []  # Terminal state
}

class MerchantService:
    """Business logic for merchant operations"""
    
    def __init__(
        self,
        repository: MerchantRepository,
        publisher: MerchantEventPublisher,
        logger: ServiceLogger,
        # redis_client: redis.Redis
    ):
        self.repository = repository
        self.publisher = publisher
        self.logger = logger
        # self.redis = redis_client
    
    async def sync_merchant(self, data: MerchantSync, idempotency_key: Optional[str] = None) -> MerchantSyncOut:
        """Sync merchant from OAuth flow"""
        correlation_id = get_correlation_context()
        
        self.logger.info(
            f"Syncing merchant: {data.shop_domain}",
            extra={
                "correlation_id": correlation_id,
                "shop_domain": data.shop_domain,
                "shop_gid": data.shop_gid
            }
        )
        
        # Validate domain
        if not data.shop_domain.lower().endswith('.myshopify.com'):
            raise InvalidDomainError(f"Invalid shop domain: {data.shop_domain}")
        
        # Check idempotency
        # if idempotency_key:
        #     cached = await self.redis.get(f"idem:{idempotency_key}")
        #     if cached:
        #         import json
        #         return MerchantSyncOut(**json.loads(cached))
        
        # Find existing merchant
        existing = await self.repository.find_by_domain_or_gid(data.shop_domain, data.shop_gid)
        
        if existing:
            # Reinstall case
            merchant = await self.repository.update_for_reinstall(existing.id, data)
            created = False
        else:
            # New install
            merchant = await self.repository.create(data)
            created = True
            
            # Publish merchant created event
            await self.publisher.publish_merchant_created(
                merchant_id=merchant.id,
                shop_gid=merchant.shop_gid,
                shop_domain=merchant.shop_domain,
                shop_name=merchant.shop_name,
                email=merchant.email,
                timezone=merchant.timezone,
                currency=merchant.currency,
                platform=merchant.platform,
                installed_at=merchant.installed_at,
                install_source=merchant.install_source
            )
        
        # Always publish synced event
        await self.publisher.publish_merchant_synced(
            merchant_id=merchant.id,
            shop_gid=merchant.shop_gid,
            shop_domain=merchant.shop_domain,
            first_install=created,
            last_auth_at=data.auth_at,
            scopes=data.scopes
        )
        
        result = MerchantSyncOut(created=created, merchant_id=merchant.id)
        
        # # Cache if idempotent
        # if idempotency_key:
        #     import json
        #     await self.redis.setex(
        #         f"idem:{idempotency_key}",
        #         3600,
        #         json.dumps(result.model_dump())
        #     )
        
        return result
    
    async def get_merchant_by_domain(self, shop_domain: str) -> MerchantOut:
        """Get merchant by shop domain"""
        merchant = await self.repository.find_by_domain(shop_domain)
        if not merchant:
            raise MerchantNotFoundError(f"Merchant not found: {shop_domain}")
        
        # Get settings to check if any consent is accepted
        settings = await self.repository.get_settings(merchant.id)
        settings_accepted = bool(settings and (settings.data_access or settings.auto_sync or settings.tos))
        
        return MerchantOut(
            merchant_id=merchant.id,
            shop_domain=merchant.shop_domain,
            shop_gid=merchant.shop_gid,
            shop_name=merchant.shop_name,
            email=merchant.email,
            timezone=merchant.timezone,
            currency=merchant.currency,
            installed_at=merchant.installed_at,
            uninstalled_at=merchant.uninstalled_at,
            last_auth_at=merchant.last_auth_at,
            last_activity_at=merchant.last_activity_at,
            status=merchant.status,
            status_reason=merchant.status_reason,
            settings_accepted=settings_accepted
        )
    
    async def get_settings(self, shop_domain: str) -> MerchantSettingsOut:
        """Get merchant settings"""
        merchant = await self.repository.find_by_domain(shop_domain)
        if not merchant:
            raise MerchantNotFoundError(f"Merchant not found: {shop_domain}")
        
        settings = await self.repository.get_settings(merchant.id)
        if not settings:
            # Create default settings if missing
            settings = await self.repository.update_settings(
                merchant.id,
                MerchantSettingsUpdate(data_access=False, auto_sync=False, tos=False)
            )
        
        return MerchantSettingsOut(
            data_access=settings.data_access,
            auto_sync=settings.auto_sync,
            tos=settings.tos
        )
    
    async def update_settings(self, shop_domain: str, updates: MerchantSettingsUpdate, ip: Optional[str] = None, user_agent: Optional[str] = None) -> MerchantSettingsOut:
        """Update merchant settings"""
        merchant = await self.repository.find_by_domain(shop_domain)
        if not merchant:
            raise MerchantNotFoundError(f"Merchant not found: {shop_domain}")
        
        # Get current settings
        current_settings = await self.repository.get_settings(merchant.id)
        if not current_settings:
            # Create default settings if missing
            current_settings = await self.repository.update_settings(
                merchant.id,
                MerchantSettingsUpdate(data_access=False, auto_sync=False, tos=False)
            )
        
        # Track changes
        changes = {}
        consent_map = {
            'data_access': ConsentType.DATA_ACCESS,
            'auto_sync': ConsentType.AUTO_SYNC,
            'tos': ConsentType.TOS
        }
        
        for field, value in updates.model_dump(exclude_unset=True).items():
            if value is not None:
                current_value = getattr(current_settings, field)
                if current_value != value:
                    changes[field] = value
                    
                    # Log consent change
                    await self.repository.create_consent_audit(
                        merchant_id=merchant.id,
                        consent_type=consent_map[field],
                        accepted=value,
                        source="ui",
                        ip=ip,
                        user_agent=user_agent
                    )
        
        # Update settings if there are changes
        if changes:
            updated_settings = await self.repository.update_settings(merchant.id, updates)
            
            # Publish settings updated event
            await self.publisher.publish_settings_updated(
                merchant_id=merchant.id,
                shop_gid=merchant.shop_gid,
                shop_domain=merchant.shop_domain,
                changes=changes,
                updated_at=datetime.utcnow()
            )
        else:
            updated_settings = current_settings
        
        return MerchantSettingsOut(
            data_access=updated_settings.data_access,
            auto_sync=updated_settings.auto_sync,
            tos=updated_settings.tos
        )
    
    async def record_activity(self, shop_domain: str, activity: MerchantActivity) -> None:
        """Record merchant activity"""
        merchant = await self.repository.find_by_domain(shop_domain)
        if not merchant:
            raise MerchantNotFoundError(f"Merchant not found: {shop_domain}")
        
        # Update last activity timestamp
        await self.repository.update_last_activity(merchant.id)
        
        # Publish activity event
        await self.publisher.publish_activity_recorded(
            merchant_id=merchant.id,
            shop_gid=merchant.shop_gid,
            activity_type=activity.activity_type,
            activity_name=activity.activity_name,
            activity_data=activity.activity_data,
            timestamp=datetime.utcnow()
        )
    
    async def update_merchant_status(self, merchant_id: str, new_status: MerchantStatus, reason: str) -> None:
        """Update merchant status with validation"""
        merchant = await self.repository.find_by_gid(merchant_id)
        if not merchant:
            merchant = await self.repository.find_by_domain(merchant_id)
        if not merchant:
            raise MerchantNotFoundError(f"Merchant not found: {merchant_id}")
        
        old_status = merchant.status
        
        # Validate transition
        if new_status not in STATUS_TRANSITIONS.get(old_status, []):
            raise InvalidStatusTransitionError(
                f"Invalid status transition from {old_status} to {new_status}"
            )
        
        # Update status
        await self.repository.update_status(merchant.id, new_status, reason, old_status)
        
        # Publish status changed event
        await self.publisher.publish_status_changed(
            merchant_id=merchant.id,
            shop_gid=merchant.shop_gid,
            old_status=old_status,
            new_status=new_status,
            reason=reason,
            changed_at=datetime.utcnow()
        )
    
    async def handle_app_uninstalled(self, shop_domain: str, uninstall_reason: Optional[str] = None) -> None:
        """Handle app uninstalled webhook"""
        merchant = await self.repository.find_by_domain(shop_domain)
        if not merchant:
            self.logger.warning(
                f"Uninstall event for unknown merchant: {shop_domain}",
                extra={"shop_domain": shop_domain}
            )
            return
        
        # Update status to DEACTIVATED
        await self.update_merchant_status(merchant.id, MerchantStatus.DEACTIVATED, "app_uninstalled")
        
        # Mark as uninstalled
        await self.repository.mark_uninstalled(merchant.id, uninstall_reason)
        
        # Publish uninstalled event
        await self.publisher.publish_merchant_uninstalled(
            merchant_id=merchant.id,
            shop_gid=merchant.shop_gid,
            shop_domain=merchant.shop_domain,
            uninstalled_at=datetime.utcnow(),
            uninstall_reason=uninstall_reason
        )

