# src/services/bulk_operation_service.py
import asyncio
from typing import Dict, Any, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import httpx
from shared.utils.logger import ServiceLogger
from ..repositories.bulk_operation_repository import BulkOperationRepository
from ..repositories.fetch_operation_repository import FetchOperationRepository
from ..services.shopify_client import ShopifyGraphQLClient
from ..services.product_transformer import ProductTransformer
from ..schemas.sync_request import SyncFetchRequestIn
from ..schemas.product import ProductsBatchOut, ProductVariantOut
from ..models.bulk_operation import BulkOperation, BulkOperationStatus
from ..models.fetch_operation import FetchOperation
from ..exceptions import BulkOperationError, BulkOperationTimeoutError, ShopifyAPIError
from ..config import ConnectorServiceConfig
from ..events.publishers import ConnectorEventPublisher

class BulkOperationService:
    """Manages Shopify bulk operations"""
    
    def __init__(
        self,
        bulk_repo: BulkOperationRepository,
        fetch_repo: FetchOperationRepository,
        transformer: ProductTransformer,
        publisher: ConnectorEventPublisher,
        logger: ServiceLogger,
        config: ConnectorServiceConfig
    ):
        self.bulk_repo = bulk_repo
        self.fetch_repo = fetch_repo
        self.transformer = transformer
        self.publisher = publisher
        self.logger = logger
        self.config = config
    
    async def start_fetch_operation(
        self, 
        sync_request: SyncFetchRequestIn,
        correlation_id: str
    ) -> FetchOperation:
        """Start a fetch operation for sync request"""
        self.logger.info(f"Starting fetch operation for sync {sync_request.sync_id}")
        
        # Create fetch operation record
        fetch_op = FetchOperation(
            sync_id=sync_request.sync_id,
            shop_id=sync_request.shop_id,
            sync_type=sync_request.sync_type,
            since_timestamp=self._parse_since_timestamp(sync_request.options),
            force_reanalysis=sync_request.options.get("force_reanalysis", False),
            status="started"
        )
        await self.fetch_repo.save(fetch_op)
        
        try:
            # Get shop credentials (in real implementation, this would come from database)
            shop_domain, access_token = await self._get_shop_credentials(sync_request.shop_id)
            
            # Build GraphQL query
            query = self._build_products_query(sync_request)
            
            # Start bulk operation
            async with ShopifyGraphQLClient(self.config, self.logger) as client:
                bulk_result = await client.start_bulk_operation(shop_domain, access_token, query)
                
                # Create bulk operation record
                bulk_op = BulkOperation(
                    sync_id=sync_request.sync_id,
                    shop_id=sync_request.shop_id,
                    shopify_bulk_id=bulk_result["id"],
                    status=bulk_result["status"],
                    graphql_query=query
                )
                await self.bulk_repo.save(bulk_op)
                
                # Update fetch operation with bulk ID
                fetch_op.bulk_operation_id = bulk_op.id
                fetch_op.status = "processing"
                await self.fetch_repo.save(fetch_op)
                
                # Start polling for completion
                asyncio.create_task(self._poll_bulk_operation(
                    bulk_op.id, 
                    shop_domain, 
                    access_token,
                    correlation_id
                ))
                
                return fetch_op
                
        except Exception as e:
            self.logger.error(f"Failed to start fetch operation: {e}")
            fetch_op.status = "failed"
            fetch_op.error_message = str(e)
            fetch_op.completed_at = datetime.utcnow()
            await self.fetch_repo.save(fetch_op)
            raise
    
    async def _poll_bulk_operation(
        self,
        bulk_op_id: UUID,
        shop_domain: str,
        access_token: str,
        correlation_id: str
    ):
        """Poll bulk operation until completion"""
        try:
            start_time = datetime.utcnow()
            timeout = timedelta(seconds=self.config.shopify_bulk_timeout_sec)
            
            while datetime.utcnow() - start_time < timeout:
                bulk_op = await self.bulk_repo.find_by_id(bulk_op_id)
                if not bulk_op:
                    self.logger.error(f"Bulk operation {bulk_op_id} not found")
                    return
                
                # Check status via API
                async with ShopifyGraphQLClient(self.config, self.logger) as client:
                    status_result = await client.get_bulk_operation_status(
                        shop_domain, access_token, bulk_op.shopify_bulk_id
                    )
                
                # Update bulk operation
                bulk_op.status = status_result["status"]
                bulk_op.object_count = status_result.get("objectCount")
                bulk_op.file_size = status_result.get("fileSize")
                bulk_op.download_url = status_result.get("url")
                bulk_op.partial_data_url = status_result.get("partialDataUrl")
                bulk_op.error_code = status_result.get("errorCode")
                
                if status_result.get("completedAt"):
                    bulk_op.completed_at = datetime.fromisoformat(
                        status_result["completedAt"].replace('Z', '+00:00')
                    )
                
                await self.bulk_repo.save(bulk_op)
                
                if bulk_op.status == BulkOperationStatus.COMPLETED:
                    self.logger.info(f"Bulk operation {bulk_op_id} completed")
                    await self._process_bulk_results(bulk_op, correlation_id)
                    return
                elif bulk_op.status == BulkOperationStatus.FAILED:
                    self.logger.error(f"Bulk operation {bulk_op_id} failed: {bulk_op.error_code}")
                    await self._handle_bulk_failure(bulk_op)
                    return
                elif bulk_op.status in [BulkOperationStatus.CREATED, BulkOperationStatus.RUNNING]:
                    # Keep polling
                    await asyncio.sleep(self.config.shopify_bulk_poll_interval_sec)
                else:
                    self.logger.warning(f"Unknown bulk operation status: {bulk_op.status}")
                    await asyncio.sleep(self.config.shopify_bulk_poll_interval_sec)
            
            # Timeout
            self.logger.error(f"Bulk operation {bulk_op_id} timed out")
            await self._handle_bulk_timeout(bulk_op)
            
        except Exception as e:
            self.logger.error(f"Error polling bulk operation {bulk_op_id}: {e}")
            bulk_op = await self.bulk_repo.find_by_id(bulk_op_id)
            if bulk_op:
                await self._handle_bulk_failure(bulk_op, str(e))
    
    async def _process_bulk_results(self, bulk_op: BulkOperation, correlation_id: str):
        """Process completed bulk operation results"""
        if not bulk_op.download_url:
            self.logger.error(f"No download URL for bulk operation {bulk_op.id}")
            return
        
        try:
            # Download JSONL data
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(bulk_op.download_url)
                response.raise_for_status()
                jsonl_data = response.text
            
            # Transform products
            products = self.transformer.transform_shopify_products(jsonl_data, bulk_op.shop_id)
            
            if not products:
                self.logger.warning(f"No products found in bulk operation {bulk_op.id}")
                await self._complete_fetch_operation(bulk_op, 0, 0)
                return
            
            # Send products in batches
            batch_size = self.config.batch_size
            total_batches = (len(products) + batch_size - 1) // batch_size
            
            for i in range(0, len(products), batch_size):
                batch = products[i:i + batch_size]
                batch_number = (i // batch_size) + 1
                
                # Create batch event
                batch_event = ProductsBatchOut(
                    event_id=str(uuid4()),
                    sync_id=bulk_op.sync_id,
                    shop_id=bulk_op.shop_id,
                    bulk_operation_id=bulk_op.shopify_bulk_id,
                    batch_number=batch_number,
                    total_batches=total_batches,
                    products=batch
                )
                
                # Publish batch to catalog service
                await self.publisher.publish_products_fetched(batch_event, correlation_id)
                
                self.logger.info(f"Published batch {batch_number}/{total_batches} with {len(batch)} products")
            
            # Complete fetch operation
            await self._complete_fetch_operation(bulk_op, len(products), total_batches)
            
        except Exception as e:
            self.logger.error(f"Failed to process bulk results for {bulk_op.id}: {e}")
            await self._handle_bulk_failure(bulk_op, str(e))
    
    async def _complete_fetch_operation(self, bulk_op: BulkOperation, product_count: int, batch_count: int):
        """Mark fetch operation as completed"""
        fetch_op = await self.fetch_repo.find_by_sync_id(bulk_op.sync_id)
        if fetch_op:
            fetch_op.status = "completed"
            fetch_op.total_products_fetched = product_count
            fetch_op.total_batches_published = batch_count
            fetch_op.completed_at = datetime.utcnow()
            await self.fetch_repo.save(fetch_op)
    
    async def _handle_bulk_failure(self, bulk_op: BulkOperation, error_message: Optional[str] = None):
        """Handle bulk operation failure"""
        fetch_op = await self.fetch_repo.find_by_sync_id(bulk_op.sync_id)
        if fetch_op:
            fetch_op.status = "failed"
            fetch_op.error_message = error_message or f"Bulk operation failed: {bulk_op.error_code}"
            fetch_op.completed_at = datetime.utcnow()
            await self.fetch_repo.save(fetch_op)
    
    async def _handle_bulk_timeout(self, bulk_op: BulkOperation):
        """Handle bulk operation timeout"""
        bulk_op.status = BulkOperationStatus.FAILED
        bulk_op.error_code = "TIMEOUT"
        bulk_op.completed_at = datetime.utcnow()
        await self.bulk_repo.save(bulk_op)
        
        await self._handle_bulk_failure(bulk_op, "Bulk operation timed out")
    
    def _build_products_query(self, sync_request: SyncFetchRequestIn) -> str:
        """Build GraphQL query for products"""
        # Base query for all products with variants
        base_query = """
        {
          products(first: 250{query_filter}) {
            edges {
              node {
                id
                title
                description
                vendor
                productType
                tags
                publishedAt
                createdAt
                updatedAt
                variants(first: 250) {
                  edges {
                    node {
                      id
                      title
                      sku
                      price
                      inventoryQuantity
                      selectedOptions {
                        name
                        value
                      }
                      image {
                        id
                        url
                        altText
                      }
                    }
                  }
                }
                images(first: 10) {
                  edges {
                    node {
                      id
                      url
                      altText
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        # Add query filter for incremental sync
        query_filter = ""
        if sync_request.sync_type == "incremental":
            since_timestamp = sync_request.options.get("since_timestamp")
            if since_timestamp:
                query_filter = f', query: "updated_at:>=\'{since_timestamp}\'"'
        
        return base_query.format(query_filter=query_filter)
    
    def _parse_since_timestamp(self, options: Dict[str, Any]) -> Optional[datetime]:
        """Parse since timestamp from options"""
        since_str = options.get("since_timestamp")
        if not since_str:
            return None
        
        try:
            return datetime.fromisoformat(since_str.replace('Z', '+00:00'))
        except Exception:
            return None
    
    async def _get_shop_credentials(self, shop_id: str) -> Tuple[str, str]:
        """Get shop domain and access token (placeholder implementation)"""
        # In real implementation, this would query a database
        # For now, return from environment variables or configuration
        shop_domain = os.getenv(f"SHOPIFY_SHOP_{shop_id}_DOMAIN", f"shop{shop_id}.myshopify.com")
        access_token = os.getenv(f"SHOPIFY_SHOP_{shop_id}_TOKEN", "test_token")
        
        return shop_domain, access_token
