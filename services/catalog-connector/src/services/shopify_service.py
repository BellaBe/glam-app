# File: services/connector-service/src/services/shopify_service.py

"""Shopify-specific service logic."""

from typing import List, Optional, Set
from datetime import datetime
import asyncio

from shared.utils.logger import ServiceLogger
from ..clients.shopify_client import ShopifyClient
from ..mappers.shopify_mapper import ShopifyMapper
from ..models.store_connection import StoreConnection
from ..schemas.catalog import CatalogItem, CatalogItemBatch, CatalogDiffBatch
from ..exceptions import ShopifyAPIError, InvalidCredentialsError
from .rate_limit_service import RateLimitService


class ShopifyService:
    """Service for Shopify API operations."""
    
    def __init__(
        self,
        rate_limit_service: RateLimitService,
        logger: ServiceLogger,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.rate_limit_service = rate_limit_service
        self.logger = logger
        self.timeout = timeout
        self.max_retries = max_retries
        self.mapper = ShopifyMapper()
    
    async def validate_connection(self, connection: StoreConnection) -> bool:
        """Validate store connection."""
        async with ShopifyClient(
            shop_domain=connection.shopify_domain,
            access_token=connection.access_token,
            api_version=connection.api_version,
            timeout=self.timeout,
            max_retries=1,  # Quick validation
            logger=self.logger
        ) as client:
            try:
                # Try to fetch product count as validation
                response = await client.get_product_count()
                return response.success
                
            except ShopifyAPIError as e:
                if e.status_code == 401:
                    raise InvalidCredentialsError(connection.store_id)
                raise
    
    async def fetch_products(
        self,
        connection: StoreConnection,
        page: int = 1,
        limit: int = 250,
        cursor: Optional[str] = None,
        fields: Optional[List[str]] = None
    ) -> CatalogItemBatch:
        """Fetch products from Shopify."""
        endpoint = "/products"
        
        async with self.rate_limit_service.rate_limit_context(
            connection.store_id,
            endpoint
        ):
            async with ShopifyClient(
                shop_domain=connection.shopify_domain,
                access_token=connection.access_token,
                api_version=connection.api_version,
                timeout=self.timeout,
                max_retries=self.max_retries,
                logger=self.logger
            ) as client:
                # Fetch products
                response = await client.get_products(
                    limit=limit,
                    page_info=cursor,
                    fields=fields
                )
                
                if not response.success:
                    raise ShopifyAPIError(
                        f"Failed to fetch products: {response.error}",
                        status_code=response.status_code
                    )
                
                # Update rate limit from headers
                if response.headers:
                    current, limit = client._parse_rate_limit(response.headers)
                    await self.rate_limit_service.update_from_headers(
                        connection.store_id,
                        endpoint,
                        current,
                        limit
                    )
                
                # Map products
                products = response.data.get("products", [])
                items = self.mapper.map_products_batch(products)
                
                # Check for more pages
                next_cursor = response.data.get("next_cursor")
                has_more = next_cursor is not None
                
                return CatalogItemBatch(
                    page=page,
                    items=items,
                    has_more=has_more,
                    cursor=next_cursor
                )
    
    async def fetch_products_diff(
        self,
        connection: StoreConnection,
        since: datetime,
        page: int = 1,
        limit: int = 250,
        cursor: Optional[str] = None
    ) -> CatalogDiffBatch:
        """Fetch changed products since timestamp."""
        endpoint = "/products"
        
        async with self.rate_limit_service.rate_limit_context(
            connection.store_id,
            endpoint
        ):
            async with ShopifyClient(
                shop_domain=connection.shopify_domain,
                access_token=connection.access_token,
                api_version=connection.api_version,
                timeout=self.timeout,
                max_retries=self.max_retries,
                logger=self.logger
            ) as client:
                # Fetch updated products
                response = await client.get_products(
                    limit=limit,
                    page_info=cursor,
                    updated_at_min=since
                )
                
                if not response.success:
                    raise ShopifyAPIError(
                        f"Failed to fetch product diff: {response.error}",
                        status_code=response.status_code
                    )
                
                # Update rate limit
                if response.headers:
                    current, limit = client._parse_rate_limit(response.headers)
                    await self.rate_limit_service.update_from_headers(
                        connection.store_id,
                        endpoint,
                        current,
                        limit
                    )
                
                # Map products
                products = response.data.get("products", [])
                items = self.mapper.map_products_batch(products)
                
                # For deletions, we'd need to track all IDs and compare
                # This is simplified - in production, you'd want a more sophisticated approach
                deleted_ids = []  # Would need to implement deletion detection
                
                # Check for more pages
                next_cursor = response.data.get("next_cursor")
                has_more = next_cursor is not None
                
                return CatalogDiffBatch(
                    page=page,
                    items=items,
                    deleted_ids=deleted_ids,
                    has_more=has_more,
                    cursor=next_cursor
                )
    
    async def fetch_all_products(
        self,
        connection: StoreConnection,
        fields: Optional[List[str]] = None,
        max_pages: Optional[int] = None
    ) -> List[CatalogItem]:
        """Fetch all products with automatic pagination."""
        all_items = []
        cursor = None
        page = 1
        
        while True:
            batch = await self.fetch_products(
                connection=connection,
                page=page,
                cursor=cursor,
                fields=fields
            )
            
            all_items.extend(batch.items)
            
            if not batch.has_more:
                break
                
            if max_pages and page >= max_pages:
                self.logger.warning(
                    f"Reached max pages limit ({max_pages})",
                    extra={"store_id": connection.store_id}
                )
                break
            
            cursor = batch.cursor
            page += 1
            
            # Small delay between pages to be nice to the API
            await asyncio.sleep(0.25)
        
        self.logger.info(
            f"Fetched {len(all_items)} products in {page} pages",
            extra={"store_id": connection.store_id}
        )
        
        return all_items