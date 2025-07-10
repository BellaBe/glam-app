# services/credit-service/src/services/plugin_status_service.py
"""Service for checking plugin status based on credit balance."""

import json
from decimal import Decimal
from uuid import UUID


import redis.asyncio as redis
from shared.utils.logger import ServiceLogger
from shared.errors import NotFoundError

from ..config import ServiceConfig
from ..repositories.credit_account_repository import CreditAccountRepository
from ..schemas.plugin_status import PluginStatusResponse, PluginStatus, BatchPluginStatusResponse
from ..schemas.plugin_status import PluginStatusRequest, BatchPluginStatusRequest
from ..metrics import increment_plugin_status_check



class PluginStatusService:
    """Service for checking plugin status based on credits"""
    
    def __init__(
        self,
        config: ServiceConfig,
        account_repo: CreditAccountRepository,
        redis_client: redis.Redis,
        logger: ServiceLogger
    ):
        self.config = config
        self.account_repo = account_repo
        self.redis = redis_client
        self.logger = logger
    
    async def get_plugin_status(self, merchant_id: UUID) -> PluginStatusResponse:
        """Get plugin status for merchant with caching"""
        
        cache_key = f"plugin_status:{merchant_id}"
        
        try:
            # Check cache first
            cached = await self.redis.get(cache_key)
            if cached:
                data = json.loads(cached)
                status = PluginStatusResponse(**data)
                increment_plugin_status_check(status.status)
                return status
            
            # Get account from database
            account = await self.account_repo.find_by_merchant_id(merchant_id)
            
            
            if not account:
                raise NotFoundError(
                    f"Credit account not found for merchant {merchant_id}"
                )
            
            else:
                # Determine status based on balance
                result = PluginStatusResponse(status=PluginStatus.ENABLED) if account.balance > Decimal("0.00") else PluginStatusResponse(status=PluginStatus.DISABLED)

            # Cache result
            await self.redis.setex(
                cache_key,
                self.config.PLUGIN_STATUS_CACHE_TTL,
                result.model_dump_json()
            )

            increment_plugin_status_check(result.status)

            self.logger.debug(
                "Plugin status checked",
                merchant_id=str(merchant_id),
                status=result.status,
                balance=float(account.balance)
            )

            return result

        except Exception as e:
            self.logger.error(
                "Failed to get plugin status",
                merchant_id=str(merchant_id),
                error=str(e),
                exc_info=True
            )
            
            # Return disabled status on error to avoid breaking plugins
            increment_plugin_status_check(PluginStatus.DISABLED)
            return PluginStatusResponse(status=PluginStatus.DISABLED)
    
    async def invalidate_cache(self, merchant_id: UUID) -> None:
        """Invalidate plugin status cache for merchant"""
        cache_key = f"plugin_status:{merchant_id}"
        
        try:
            await self.redis.delete(cache_key)
            self.logger.debug(
                "Plugin status cache invalidated",
                merchant_id=str(merchant_id)
            )
        except Exception as e:
            self.logger.warning(
                "Failed to invalidate plugin status cache",
                merchant_id=str(merchant_id),
                error=str(e)
            )
    
    async def bulk_get_plugin_status(
        self, 
        merchant_ids: list[UUID]
    ) -> BatchPluginStatusResponse:
        """Get plugin status for multiple merchants"""
        
        results = {}
        
        for merchant_id in merchant_ids:
            try:
                status = await self.get_plugin_status(merchant_id)
                results[str(merchant_id)] = status
            except Exception as e:
                self.logger.error(
                    "Failed to get plugin status in bulk",
                    merchant_id=str(merchant_id),
                    error=str(e)
                )
                results[str(merchant_id)] = PluginStatusResponse(status=PluginStatus.DISABLED)

        return BatchPluginStatusResponse(statuses=results)