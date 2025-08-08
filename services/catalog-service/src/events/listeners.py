from shared.messaging.listener import Listener
from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger
from ..services.cache_service import CacheService
from ..services.catalog_sync_service import CatalogSyncService
from ..repositories.catalog_state_repository import CatalogStateRepository
from ..repositories.sync_job_repository import SyncJobRepository

class MerchantSettingsListener(Listener):
    """Listen for merchant settings updates"""
    
    @property
    def subject(self) -> str:
        return "evt.merchant.settings.updated"
    
    @property
    def queue_group(self) -> str:
        return "catalog-merchant-settings"
    
    @property
    def service_name(self) -> str:
        return "catalog-service"
    
    def __init__(
        self,
        js_client: JetStreamClient,
        cache_service: CacheService,
        catalog_state_repo: CatalogStateRepository,
        logger: ServiceLogger
    ):
        super().__init__(js_client, logger)
        self.cache_service = cache_service
        self.catalog_state_repo = catalog_state_repo
    
    async def on_message(self, data: dict) -> None:
        """Handle merchant settings update"""
        shop_domain = data["shopDomain"]
        
        # Update cache
        await self.cache_service.set_merchant_settings(shop_domain, {
            "dataAccess": data.get("dataAccess", False),
            "autoSync": data.get("autoSync", False),
            "tos": data.get("tos", False)
        })
        
        # Update database
        await self.catalog_state_repo.update_settings(
            shop_domain,
            data.get("dataAccess", False),
            data.get("autoSync", False),
            data.get("tos", False)
        )
        
        self.logger.info(f"Updated merchant settings for {shop_domain}")

class BillingEntitlementsListener(Listener):
    """Listen for billing entitlement changes"""
    
    @property
    def subject(self) -> str:
        return "evt.billing.entitlements.changed"
    
    @property
    def queue_group(self) -> str:
        return "catalog-billing-entitlements"
    
    @property
    def service_name(self) -> str:
        return "catalog-service"
    
    def __init__(
        self,
        js_client: JetStreamClient,
        cache_service: CacheService,
        catalog_state_repo: CatalogStateRepository,
        logger: ServiceLogger
    ):
        super().__init__(js_client, logger)
        self.cache_service = cache_service
        self.catalog_state_repo = catalog_state_repo
    
    async def on_message(self, data: dict) -> None:
        """Handle billing entitlements update"""
        shop_domain = data["shopDomain"]
        
        # Update cache
        await self.cache_service.set_billing_entitlements(shop_domain, {
            "entitled": data.get("entitled", False),
            "trialActive": data.get("trialActive", False),
            "subscriptionActive": data.get("subscriptionActive", False)
        })
        
        # Update database
        await self.catalog_state_repo.update_entitlements(
            shop_domain,
            data.get("entitled", False)
        )
        
        self.logger.info(f"Updated billing entitlements for {shop_domain}")

class CatalogCountedListener(Listener):
    """Listen for catalog count from platform connector"""
    
    @property
    def subject(self) -> str:
        return "evt.connector.shopify.catalog.counted"
    
    @property
    def queue_group(self) -> str:
        return "catalog-counted"
    
    @property
    def service_name(self) -> str:
        return "catalog-service"
    
    def __init__(
        self,
        js_client: JetStreamClient,
        sync_job_repo: SyncJobRepository,
        logger: ServiceLogger
    ):
        super().__init__(js_client, logger)
        self.sync_job_repo = sync_job_repo
    
    async def on_message(self, data: dict) -> None:
        """Handle catalog count event"""
        sync_id = data["syncId"]
        
        # Update counts
        await self.sync_job_repo.update_counts(
            sync_id,
            data["products"],
            data["variants"]
        )
        
        self.logger.info(
            f"Updated catalog counts for sync {sync_id}",
            extra={
                "products": data["products"],
                "variants": data["variants"]
            }
        )

class CatalogItemListener(Listener):
    """Listen for catalog items from platform connector"""
    
    @property
    def subject(self) -> str:
        return "evt.connector.shopify.catalog.item"
    
    @property
    def queue_group(self) -> str:
        return "catalog-items"
    
    @property
    def service_name(self) -> str:
        return "catalog-service"
    
    def __init__(
        self,
        js_client: JetStreamClient,
        sync_service: CatalogSyncService,
        logger: ServiceLogger
    ):
        super().__init__(js_client, logger)
        self.sync_service = sync_service
    
    async def on_message(self, data: dict) -> None:
        """Handle catalog item event"""
        await self.sync_service.handle_catalog_item(data)

class AnalysisCompletedListener(Listener):
    """Listen for analysis completion events"""
    
    @property
    def subject(self) -> str:
        return "evt.analysis.completed"
    
    @property
    def queue_group(self) -> str:
        return "catalog-analysis-completed"
    
    @property
    def service_name(self) -> str:
        return "catalog-service"
    
    def __init__(
        self,
        js_client: JetStreamClient,
        sync_service: CatalogSyncService,
        logger: ServiceLogger
    ):
        super().__init__(js_client, logger)
        self.sync_service = sync_service
    
    async def on_message(self, data: dict) -> None:
        """Handle analysis completion event"""
        await self.sync_service.handle_analysis_completed(data)

# ================================================================
