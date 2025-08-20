# services/platform-connector/src/services/connector_service.py (updated)
from typing import Dict, Any, Optional
import asyncio

from shared.utils.logger import ServiceLogger
from shared.utils.exceptions import (
    NotFoundError,
    InfrastructureError,
    UnauthorizedError
)

from ..adapters.shopify import ShopifyAdapter
from ..adapters.woocommerce import WooCommerceAdapter
from .token_service import TokenServiceClient

class ConnectorService:
    """Orchestrates platform connections with Token Service integration"""
    
    def __init__(
        self,
        event_publisher,
        logger: ServiceLogger,
        config: dict
    ):
        self.event_publisher = event_publisher
        self.logger = logger
        self.config = config
        
        # Initialize Token Service client
        self.token_client = TokenServiceClient(logger, config)
        
        # Initialize adapters with token client
        self.adapters = {
            "shopify": ShopifyAdapter(logger, config, self.token_client),
            "woocommerce": WooCommerceAdapter(logger, config, self.token_client)
        }
    
    async def process_sync_request(
        self,
        merchant_id: str,
        platform_name: str,
        platform_id: str,
        platform_domain: str,
        sync_id: str,
        correlation_id: str
    ) -> None:
        """Process catalog sync request with token retrieval"""
        
        self.logger.info(
            f"Processing sync request for {platform_name}",
            extra={
                "correlation_id": correlation_id,
                "sync_id": sync_id,
                "merchant_id": merchant_id,
                "platform": platform_name,
                "domain": platform_domain
            }
        )
        
        # Get appropriate adapter
        adapter = self.adapters.get(platform_name)
        if not adapter:
            await self.event_publisher.platform_fetch_failed(
                merchant_id=merchant_id,
                sync_id=sync_id,
                error=f"Platform {platform_name} not supported",
                correlation_id=correlation_id
            )
            raise NotFoundError(
                f"Platform adapter not found: {platform_name}",
                resource="platform_adapter",
                resource_id=platform_name
            )
        
        try:
            # Fetch products in batches (adapter will get token from Token Service)
            total_products = 0
            batch_count = 0
            
            async for batch in adapter.fetch_products(
                merchant_id=merchant_id,
                platform_id=platform_id,
                platform_domain=platform_domain,
                sync_id=sync_id,
                correlation_id=correlation_id
            ):
                batch_count += 1
                total_products += len(batch["products"])
                
                # Publish batch to Catalog Service
                await self.event_publisher.platform_products_fetched(
                    batch_data=batch,
                    correlation_id=correlation_id
                )
                
                self.logger.info(
                    f"Published batch {batch_count} with {len(batch['products'])} products",
                    extra={
                        "correlation_id": correlation_id,
                        "sync_id": sync_id,
                        "batch_num": batch_count,
                        "has_more": batch["has_more"]
                    }
                )
            
            # Publish completion event
            await self.event_publisher.platform_fetch_completed(
                merchant_id=merchant_id,
                sync_id=sync_id,
                total_products=total_products,
                correlation_id=correlation_id
            )
            
            self.logger.info(
                f"Completed platform fetch for {platform_name}",
                extra={
                    "correlation_id": correlation_id,
                    "sync_id": sync_id,
                    "total_products": total_products,
                    "total_batches": batch_count
                }
            )
            
        except UnauthorizedError as e:
            # Authentication/token failure
            self.logger.error(
                f"Authentication failed for {platform_name}: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "sync_id": sync_id,
                    "domain": platform_domain
                }
            )
            
            await self.event_publisher.platform_fetch_failed(
                merchant_id=merchant_id,
                sync_id=sync_id,
                error=f"Authentication failed: {str(e)}",
                correlation_id=correlation_id
            )
            raise
            
        except InfrastructureError as e:
            # Platform API or Token Service error
            if e.retryable:
                self.logger.warning(
                    f"Retryable error: {e}",
                    extra={
                        "correlation_id": correlation_id,
                        "sync_id": sync_id,
                        "error": str(e)
                    }
                )
                raise  # Let listener handle retry
            else:
                await self.event_publisher.platform_fetch_failed(
                    merchant_id=merchant_id,
                    sync_id=sync_id,
                    error=str(e),
                    correlation_id=correlation_id
                )
                raise
                
        except Exception as e:
            # Unexpected error
            self.logger.error(
                f"Unexpected error during platform fetch: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "sync_id": sync_id
                },
                exc_info=True
            )
            
            await self.event_publisher.platform_fetch_failed(
                merchant_id=merchant_id,
                sync_id=sync_id,
                error=str(e),
                correlation_id=correlation_id
            )
            raise