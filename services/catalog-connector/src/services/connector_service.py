# File: services/connector-service/src/services/connector_service.py

"""Core connector business logic."""

from typing import Optional, List
from datetime import datetime, timezone
from uuid import UUID

from shared.utils.logger import ServiceLogger
from shared.events import EventContext

from ..config import ServiceConfig
from ..events.publishers import ConnectorEventPublisher
from ..repositories.store_connection_repository import StoreConnectionRepository
from ..models.store_connection import StoreConnection, StoreStatus
from ..schemas.catalog import CatalogItemBatch, CatalogDiffBatch
from ..schemas.commands import FetchItemsCommand, FetchItemsDiffCommand, ValidateStoreCommand
from ..exceptions import StoreNotFoundError, InvalidCredentialsError
from .shopify_service import ShopifyService
from .rate_limit_service import RateLimitService


class ConnectorService:
    """Core connector business logic."""
    
    def __init__(
        self,
        config: ServiceConfig,
        publisher: ConnectorEventPublisher,
        shopify_service: ShopifyService,
        rate_limit_service: RateLimitService,
        store_repository: StoreConnectionRepository,
        logger: ServiceLogger
    ):
        self.config = config
        self.publisher = publisher
        self.shopify_service = shopify_service
        self.rate_limit_service = rate_limit_service
        self.store_repo = store_repository
        self.logger = logger
    
    async def process_fetch_items(
        self,
        command: FetchItemsCommand,
        context: EventContext
    ) -> None:
        """Process fetch items command."""
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get store connection
            connection = await self._get_active_connection(command.store_id)
            
            # Update last used
            await self.store_repo.update_last_used(command.store_id)
            
            # Fetch products
            batch = await self.shopify_service.fetch_products(
                connection=connection,
                page=command.page,
                limit=command.limit,
                cursor=command.cursor,
                fields=command.fields
            )
            
            # Publish success event
            await self.publisher.publish_items_fetched(
                page=command.page,
                items=[item.model_dump() for item in batch.items],
                has_more=batch.has_more,
                cursor=batch.cursor,
                context=context
            )
            
            # Log metrics
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.logger.info(
                f"Fetched {len(batch.items)} items in {duration:.2f}s",
                extra={
                    "store_id": command.store_id,
                    "page": command.page,
                    "item_count": len(batch.items),
                    "duration": duration
                }
            )
            
        except Exception as e:
            # Publish failure event
            await self.publisher.publish_fetch_failed(
                page=command.page,
                error=str(e),
                context=context
            )
            
            # Update store status if credentials invalid
            if isinstance(e, InvalidCredentialsError):
                await self.store_repo.update_status(
                    command.store_id,
                    StoreStatus.INVALID
                )
            
            raise
    
    async def process_validate_store(
        self,
        command: ValidateStoreCommand,
        context: EventContext
    ) -> None:
        """Process validate store command."""
        try:
            # Get store connection
            connection = await self._get_connection(command.store_id)
            
            # Validate connection
            is_valid = await self.shopify_service.validate_connection(connection)
            
            # Update status
            new_status = StoreStatus.ACTIVE if is_valid else StoreStatus.INVALID
            await self.store_repo.update_status(command.store_id, new_status)
            
            # Publish result
            await self.publisher.publish_store_validated(
                store_id=command.store_id,
                is_valid=is_valid,
                context=context
            )
            
            self.logger.info(
                f"Store validation: {is_valid}",
                extra={"store_id": command.store_id, "is_valid": is_valid}
            )
            
        except Exception as e:
            # Publish validation failed
            await self.publisher.publish_store_validation_failed(
                store_id=command.store_id,
                error=str(e),
                context=context
            )
            raise
    
    async def _get_connection(self, store_id: str) -> StoreConnection:
        """Get store connection by ID."""
        connection = await self.store_repo.get_by_store_id(store_id)
        if not connection:
            raise StoreNotFoundError(store_id)
        return connection
    
    async def _get_active_connection(self, store_id: str) -> StoreConnection:
        """Get active store connection by ID."""
        connection = await self._get_connection(store_id)
        
        if connection.status != StoreStatus.ACTIVE:
            raise StoreConnectionError(
                f"Store connection is not active: {connection.status}",
                store_id=store_id,
                details={"status": connection.status}
            )
        
        return connection
    
    async def fetch_all_items_completed(
        self,
        store_id: str,
        total_fetched: int,
        duration: float,
        context: EventContext
    ) -> None:
        """Handle completion of full catalog fetch."""
        await self.publisher.publish_fetch_completed(
            store_id=store_id,
            total_fetched=total_fetched,
            duration=duration,
            context=context
        )
        
        self.logger.info(
            f"Completed full catalog fetch: {total_fetched} items in {duration:.2f}s",
            extra={
                "store_id": store_id,
                "total_fetched": total_fetched,
                "duration": duration
            }
        )
                context=context
            )
            
            # Update store status if credentials invalid
            if isinstance(e, InvalidCredentialsError):
                await self.store_repo.update_status(
                    command.store_id,
                    StoreStatus.INVALID
                )
            
            raise
    
    async def process_fetch_items_diff(
        self,
        command: FetchItemsDiffCommand,
        context: EventContext
    ) -> None:
        """Process fetch items diff command."""
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get store connection
            connection = await self._get_active_connection(command.store_id)
            
            # Update last used
            await self.store_repo.update_last_used(command.store_id)
            
            # Fetch changed products
            batch = await self.shopify_service.fetch_products_diff(
                connection=connection,
                since=command.since,
                page=command.page,
                limit=command.limit,
                cursor=command.cursor
            )
            
            # Publish success event
            await self.publisher.publish_items_diff_fetched(
                page=command.page,
                items=[item.model_dump() for item in batch.items],
                deleted_ids=batch.deleted_ids,
                has_more=batch.has_more,
                cursor=batch.cursor,
                context=context
            )
            
            # Log metrics
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.logger.info(
                f"Fetched diff: {len(batch.items)} changed, {len(batch.deleted_ids)} deleted in {duration:.2f}s",
                extra={
                    "store_id": command.store_id,
                    "page": command.page,
                    "changed_count": len(batch.items),
                    "deleted_count": len(batch.deleted_ids),
                    "duration": duration
                }
            )
            
        except Exception as e:
            # Publish failure event
            await self.publisher.publish_fetch_failed(
                page=command.page,
                error=str(e),
                context=context,
            )