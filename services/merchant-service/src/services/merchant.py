# services/merchant-service/src/services/merchant.py
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone
import redis.asyncio as redis
from shared.utils.logger import ServiceLogger
from shared.errors import NotFoundError, ConflictError
from ..config import MerchantServiceConfig
from ..repositories import MerchantRepository
from ..mappers import MerchantMapper
from ..schemas.merchant import (
    MerchantBootstrap, InstallationRecordCreate, MerchantResponse, 
    MerchantConfigUpdate, MerchantConfigResponse, ActivityRecord
)
from ..models.merchant import Merchant
from ..models.merchant_status import MerchantStatus
from ..models.merchant_configuration import MerchantConfiguration
from ..models.installation_record import InstallationRecord
from ..models.enums import MerchantStatusEnum
from ..events.publishers import MerchantEventPublisher

# Valid status transitions
STATUS_TRANSITIONS = {
    MerchantStatusEnum.PENDING: [
        MerchantStatusEnum.ONBOARDING,
        MerchantStatusEnum.DEACTIVATED
    ],
    MerchantStatusEnum.ONBOARDING: [
        MerchantStatusEnum.TRIAL,
        MerchantStatusEnum.DEACTIVATED
    ],
    MerchantStatusEnum.TRIAL: [
        MerchantStatusEnum.ACTIVE,
        MerchantStatusEnum.SUSPENDED,
        MerchantStatusEnum.DEACTIVATED
    ],
    MerchantStatusEnum.ACTIVE: [
        MerchantStatusEnum.SUSPENDED,
        MerchantStatusEnum.DEACTIVATED
    ],
    MerchantStatusEnum.SUSPENDED: [
        MerchantStatusEnum.ACTIVE,
        MerchantStatusEnum.TRIAL,
        MerchantStatusEnum.DEACTIVATED
    ],
    MerchantStatusEnum.DEACTIVATED: []  # Terminal state
}

class MerchantService:
    """Merchant service - Single source of truth for merchant identity and status"""
    
    def __init__(
        self,
        config: MerchantServiceConfig,
        merchant_repo: MerchantRepository,
        mapper: MerchantMapper,
        publisher: MerchantEventPublisher,
        redis_client: redis.Redis,
        logger: ServiceLogger
    ):
        self.config = config
        self.merchant_repo = merchant_repo
        self.mapper = mapper
        self.publisher = publisher
        self.redis_client = redis_client
        self.logger = logger
    
    async def get_merchant(self, merchant_id: UUID) -> MerchantResponse:
        """Get merchant by canonical UUID"""
        # Try cache first
        cached = await self.redis_client.get(f"merchant:{merchant_id}")
        if cached:
            # Parse cached data and return
            pass
        
        merchant = await self.merchant_repo.get_with_all_relations(merchant_id)
        if not merchant:
            raise NotFoundError(f"Merchant {merchant_id} not found")
        
        # Cache for future requests
        if self.config.cache_enabled:
            await self.redis_client.setex(
                f"merchant:{merchant_id}",
                300,  # 5 minutes
                "cached_data"  # Would serialize merchant data
            )
        
        return self.mapper.to_out(merchant)
    
    async def lookup_merchant(self, platform: str, external_id: str) -> MerchantResponse:
        """Lookup merchant by platform-specific external ID"""
        # Try cache first  
        cache_key = f"merchant_lookup:{platform}:{external_id}"
        if self.config.cache_enabled:
            cached = await self.redis_client.get(cache_key)
            if cached:
                merchant_id = UUID(cached)
                return await self.get_merchant(merchant_id)
        
        merchant = await self.merchant_repo.lookup_by_platform(platform, external_id)
        if not merchant:
            raise NotFoundError(f"Merchant not found for {platform} ID {external_id}")
        
        # Cache the lookup mapping
        if self.config.cache_enabled:
            await self.redis_client.setex(cache_key, 300, str(merchant.id))
        
        return self.mapper.to_out(merchant)
    
    async def update_merchant_configuration(
        self,
        merchant_id: UUID,
        config_updates: MerchantConfigUpdate,
        updated_by: str = "merchant"
    ) -> MerchantConfigResponse:
        """Update merchant configuration (only writable fields)"""
        merchant = await self.merchant_repo.get_with_all_relations(merchant_id)
        if not merchant:
            raise NotFoundError(f"Merchant {merchant_id} not found")
        
        current_config = merchant.configuration
        
        # Track changes
        changed_fields = []
        previous_config = {}
        
        # Only allow updates to specific writable fields
        writable_fields = {
            'widget_enabled', 'widget_position', 'widget_theme', 'widget_language',
            'widget_configuration', 'is_marketable', 'custom_css', 
            'custom_branding', 'custom_messages'
        }
        
        update_data = config_updates.model_dump(exclude_unset=True)
        for field, new_value in update_data.items():
            if field not in writable_fields:
                continue  # Skip non-writable fields
            
            if hasattr(current_config, field):
                old_value = getattr(current_config, field)
                if old_value != new_value:
                    changed_fields.append(field)
                    previous_config[field] = old_value
                    setattr(current_config, field, new_value)
        
        if changed_fields:
            # Update timestamp
            current_config.updated_at = datetime.utcnow()
            
            # Save to database
            await self.merchant_repo.update_configuration(current_config)
            
            # Invalidate cache
            if self.config.cache_enabled:
                await self.redis_client.delete(f"merchant:{merchant_id}")
            
            # Publish configuration updated event
            await self.publisher.publish_config_updated(
                merchant_id=merchant_id,
                shop_id=merchant.shop_id,
                changed_fields=changed_fields,
                previous_config=previous_config,
                new_config={field: update_data[field] for field in changed_fields},
                is_marketable=current_config.is_marketable,
                updated_by=updated_by
            )
        
        return MerchantConfigResponse.model_validate(current_config)
    
    async def record_activity(
        self,
        merchant_id: UUID,
        activity: ActivityRecord
    ):
        """Fire-and-forget activity recording - publishes event only"""
        # Update last activity timestamp
        await self.merchant_repo.update_last_activity(merchant_id)
        
        # Invalidate cache
        if self.config.cache_enabled:
            await self.redis_client.delete(f"merchant:{merchant_id}")
        
        # Publish activity event (Analytics service will persist)
        await self.publisher.publish_activity_recorded(
            merchant_id=merchant_id,
            activity_type=activity.activity_type,
            activity_name=activity.activity_name,
            activity_description=activity.activity_description,
            activity_data=activity.activity_data,
            session_id=activity.session_id,
            user_agent=activity.user_agent,
            ip_address=activity.ip_address
        )
    
    # Internal methods (used by event handlers only)
    async def create_merchant(
        self, 
        merchant_data: MerchantBootstrap, 
        installation_data: Optional[InstallationRecordCreate] = None
    ) -> MerchantResponse:
        """Create merchant (internal - called by webhook handlers only)"""
        # Check if merchant already exists
        existing = await self.merchant_repo.get_by_shop_id(merchant_data.shop_id)
        if existing:
            raise ConflictError(f"Merchant with shop_id {merchant_data.shop_id} already exists")
        
        # Create merchant
        merchant = self.mapper.to_model(merchant_data)
        merchant = await self.merchant_repo.create_merchant(merchant)
        
        if not merchant:
            raise ConflictError("Failed to create merchant")
        
        # Create initial status
        status = MerchantStatus(
            merchant_id=merchant.id,
            status=MerchantStatusEnum.PENDING,
            status_reason="merchant_created"
        )
        await self.merchant_repo.create_status(status)
        
        # Create default configuration
        config = MerchantConfiguration(merchant_id=merchant.id)
        await self.merchant_repo.create_configuration(config)
        
        # Record installation if provided
        if installation_data:
            installation = InstallationRecord(
                merchant_id=merchant.id,
                installed_at=datetime.now(timezone.utc),
                **installation_data.model_dump()
            )
            await self.merchant_repo.create_installation_record(installation)
        
        # Publish merchant created event
        await self.publisher.publish_merchant_created(
            merchant_id=merchant.id,
            shop_id=merchant.shop_id,
            shop_domain=merchant.shop_domain,
            email=merchant.email,
            platform=merchant.platform,
            is_marketable=config.is_marketable
        )
        
        return self.mapper.to_out(merchant)
    
    async def update_merchant_status(
        self,
        merchant_id: UUID,
        new_status: MerchantStatusEnum,
        reason: str,
        changed_by: str = "system"
    ) -> bool:
        """Update merchant status (internal - event handlers only)"""
        merchant = await self.merchant_repo.get_with_status(merchant_id)
        if not merchant:
            raise NotFoundError(f"Merchant {merchant_id} not found")
        
        old_status = merchant.status.status
        
        # Validate transition
        if new_status not in STATUS_TRANSITIONS[old_status]:
            raise ValueError(f"Cannot transition from {old_status} to {new_status}")
        
        # Update status
        merchant.status.previous_status = old_status
        merchant.status.status = new_status
        merchant.status.status_reason = reason
        merchant.status.changed_at = datetime.utcnow()
        merchant.status.updated_at = datetime.utcnow()
        
        # Add status-specific timestamps
        if new_status == MerchantStatusEnum.SUSPENDED:
            merchant.status.suspended_at = datetime.utcnow()
        elif new_status == MerchantStatusEnum.ACTIVE:
            merchant.status.activated_at = datetime.utcnow()
            merchant.status.suspended_at = None
        elif new_status == MerchantStatusEnum.DEACTIVATED:
            merchant.status.deactivated_at = datetime.utcnow()
        
        # Update status history
        history = merchant.status.status_history or []
        history.append({
            "from_status": old_status,
            "to_status": new_status,
            "reason": reason,
            "changed_by": changed_by,
            "changed_at": datetime.utcnow().isoformat()
        })
        merchant.status.status_history = history
        
        # Save to database
        await self.merchant_repo.update_status(merchant.status)
        
        # Invalidate cache
        if self.config.cache_enabled:
            await self.redis_client.delete(f"merchant:{merchant_id}")
        
        # Publish status changed event
        await self.publisher.publish_status_changed(
            merchant_id=merchant_id,
            shop_id=merchant.shop_id,
            old_status=old_status,
            new_status=new_status,
            reason=reason,
            changed_by=changed_by
        )
        
        return True
