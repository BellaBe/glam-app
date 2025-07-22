# src/services/catalog_service.py
from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import hashlib
from pathlib import Path
from shared.utils.logger import ServiceLogger
from ..repositories.item_repository import ItemRepository
from ..repositories.analysis_result_repository import AnalysisResultRepository
from ..mappers.item_mapper import ItemMapper
from ..schemas.item import ItemOut, ItemWithAnalysisOut, ProductSearchParams
from ..models.enums import SyncStatus, AnalysisStatus
from ..exceptions import ItemNotFoundError
from ..events.publishers import CatalogEventPublisher
from ..config import CatalogServiceConfig

class CatalogService:
    """Core catalog business logic"""
    
    def __init__(
        self,
        item_repo: ItemRepository,
        analysis_repo: AnalysisResultRepository,
        item_mapper: ItemMapper,
        publisher: CatalogEventPublisher,
        logger: ServiceLogger,
        config: CatalogServiceConfig
    ):
        self.item_repo = item_repo
        self.analysis_repo = analysis_repo
        self.item_mapper = item_mapper
        self.publisher = publisher
        self.logger = logger
        self.config = config
    
    async def get_item(self, item_id: UUID) -> ItemWithAnalysisOut:
        """Get catalog item with analysis"""
        model = await self.item_repo.find_by_id(item_id)
        if not model:
            raise ItemNotFoundError(f"Item {item_id} not found")
        
        # Get base item data
        item_out = self.item_mapper.to_out(model)
        
        # Get analysis if available
        analysis_result = await self.analysis_repo.find_by_item_id(item_id)
        analysis_data = None
        
        if analysis_result:
            analysis_data = {
                "category": analysis_result.category,
                "subcategory": analysis_result.subcategory,
                "description": analysis_result.description,
                "gender": analysis_result.gender,
                "quality_score": float(analysis_result.quality_score) if analysis_result.quality_score else None,
                "confidence_score": float(analysis_result.confidence_score) if analysis_result.confidence_score else None,
                "model_version": analysis_result.model_version,
                "processing_time_ms": analysis_result.processing_time_ms,
                "analyzed_at": analysis_result.analyzed_at,
                "attributes": json.loads(analysis_result.attributes) if analysis_result.attributes else {}
            }
        
        return ItemWithAnalysisOut(
            **item_out.model_dump(),
            analysis=analysis_data
        )
    
    async def search_products(self, params: ProductSearchParams) -> Dict[str, Any]:
        """Search products with pagination"""
        items = await self.item_repo.find_by_shop_id(
            shop_id=params.shop_id,
            limit=params.limit,
            offset=params.offset,
            category=params.category,
            status=params.status,
            search=params.search
        )
        
        total = await self.item_repo.count_by_shop_id(
            shop_id=params.shop_id,
            category=params.category,
            status=params.status,
            search=params.search
        )
        
        items_out = self.item_mapper.list_to_out(items)
        
        return {
            "products": items_out,
            "pagination": {
                "total": total,
                "limit": params.limit,
                "offset": params.offset,
                "has_next": params.offset + params.limit < total
            }
        }
    
    async def process_products_batch(
        self, 
        event_payload: Dict[str, Any],
        correlation_id: str
    ):
        """Process products batch from sync event"""
        sync_id = UUID(event_payload["sync_id"])
        shop_id = event_payload["shop_id"]
        products = event_payload.get("products", [])
        
        self.logger.info(f"Processing {len(products)} products for sync {sync_id}")
        
        analysis_items = []
        processed_count = 0
        
        for product_data in products:
            try:
                # UPSERT item using unique constraint
                item = await self._upsert_item(shop_id, product_data)
                
                # Cache image if needed
                if product_data.get("image_url") and not item.cached_image_path:
                    cached_path = await self._cache_image(shop_id, product_data["image_url"])
                    if cached_path:
                        await self.item_repo.update(item.id, {
                            "cached_image_path": cached_path
                        })
                
                # Add to analysis batch if image is cached
                if item.cached_image_path:
                    analysis_items.append({
                        "item_id": str(item.id),
                        "product_id": item.product_id,
                        "variant_id": item.variant_id,
                        "image_path": item.cached_image_path,
                        "gender": item.gender
                    })
                
                processed_count += 1
                
            except Exception as e:
                self.logger.error(f"Failed to process product {product_data.get('product_id')}: {e}")
        
        # Request analysis for batch
        if analysis_items:
            batch_id = f"batch_{sync_id}_{datetime.utcnow().timestamp()}"
            
            await self.publisher.publish_analysis_request(
                sync_id=sync_id,
                shop_id=shop_id,
                batch_id=batch_id,
                items=analysis_items,
                correlation_id=correlation_id
            )
        
        self.logger.info(f"Processed {processed_count} products, requested analysis for {len(analysis_items)}")
    
    async def process_analysis_results(
        self,
        event_payload: Dict[str, Any],
        correlation_id: str
    ):
        """Process analysis results from AI service"""
        results = event_payload.get("results", [])
        
        self.logger.info(f"Processing {len(results)} analysis results")
        
        for result_data in results:
            try:
                item_id = UUID(result_data["item_id"])
                
                # Upsert analysis result
                await self._upsert_analysis_result(item_id, result_data)
                
                # Update item status
                await self.item_repo.update(item_id, {
                    "analysis_status": AnalysisStatus.ANALYZED
                })
                
            except Exception as e:
                self.logger.error(f"Failed to process analysis result for {result_data.get('item_id')}: {e}")
    
    async def recovery_scan(self):
        """Scan for incomplete syncs and re-emit missing events"""
        if not self.config.startup_recovery_enabled:
            return
        
        self.logger.info("Starting recovery scan for incomplete syncs")
        
        cutoff_time = datetime.utcnow() - timedelta(minutes=10)
        
        # Find items needing analysis
        stuck_items = await self.item_repo.find_stuck_analysis(
            cutoff_time=cutoff_time,
            limit=self.config.reconciliation_batch_size
        )
        
        if stuck_items:
            self.logger.warning(f"Found {len(stuck_items)} items stuck in analysis")
            
            # Group by shop and re-emit analysis requests
            items_by_shop = {}
            for item in stuck_items:
                shop_id = item.shop_id
                if shop_id not in items_by_shop:
                    items_by_shop[shop_id] = []
                items_by_shop[shop_id].append(item)
            
            for shop_id, items in items_by_shop.items():
                # Update requeued timestamp
                item_ids = [item.id for item in items]
                await self.item_repo.bulk_update(
                    item_ids,
                    {"requeued_at": datetime.utcnow()}
                )
                
                # Re-emit analysis request
                analysis_items = [
                    {
                        "item_id": str(item.id),
                        "product_id": item.product_id,
                        "variant_id": item.variant_id,
                        "image_path": item.cached_image_path,
                        "gender": item.gender
                    }
                    for item in items
                    if item.cached_image_path
                ]
                
                if analysis_items:
                    batch_id = f"recovery_{int(datetime.utcnow().timestamp())}"
                    
                    await self.publisher.publish_analysis_request(
                        sync_id=UUID("00000000-0000-0000-0000-000000000000"),  # Recovery sync
                        shop_id=shop_id,
                        batch_id=batch_id,
                        items=analysis_items,
                        correlation_id="recovery"
                    )
        
        self.logger.info(f"Recovery scan completed: {len(stuck_items)} items recovered")
    
    async def _upsert_item(self, shop_id: str, product_data: Dict[str, Any]) -> Item:
        """Upsert item with conflict resolution"""
        existing = await self.item_repo.find_by_shop_and_variant(
            shop_id=shop_id,
            product_id=product_data["product_id"],
            variant_id=product_data["variant_id"]
        )
        
        item_data = {
            "shop_id": shop_id,
            "product_id": product_data["product_id"],
            "variant_id": product_data["variant_id"],
            "image_id": product_data.get("image_id"),
            "product_title": product_data.get("title"),
            "product_description": product_data.get("description"),
            "product_vendor": product_data.get("vendor"),
            "product_type": product_data.get("product_type"),
            "product_tags": product_data.get("tags", []),
            "variant_title": product_data.get("variant_title"),
            "variant_sku": product_data.get("sku"),
            "variant_price": product_data.get("price"),
            "variant_inventory": product_data.get("inventory_quantity", 0),
            "variant_options": json.dumps(product_data.get("variant_options", {})),
            "image_url": product_data.get("image_url"),
            "sync_status": SyncStatus.SYNCED,
            "synced_at": datetime.utcnow(),
            "shopify_created_at": product_data.get("shopify_created_at"),
            "shopify_updated_at": product_data.get("shopify_updated_at")
        }
        
        if existing:
            # Update existing
            for key, value in item_data.items():
                setattr(existing, key, value)
            await self.item_repo.save(existing)
            return existing
        else:
            # Create new
            model = self.item_mapper.to_model(ItemIn(**item_data))
            await self.item_repo.save(model)
            return model
    
    async def _upsert_analysis_result(self, item_id: UUID, result_data: Dict[str, Any]):
        """Upsert analysis result"""
        model_version = result_data["model_version"]
        
        existing = await self.analysis_repo.find_by_item_and_version(item_id, model_version)
        
        analysis_data = {
            "item_id": item_id,
            "model_version": model_version,
            "category": result_data.get("category"),
            "subcategory": result_data.get("subcategory"),
            "description": result_data.get("description"),
            "gender": result_data.get("gender"),
            "attributes": json.dumps(result_data.get("attributes", {})),
            "quality_score": result_data.get("quality_score"),
            "confidence_score": result_data.get("confidence_score"),
            "processing_time_ms": result_data.get("processing_time_ms"),
            "analyzed_at": datetime.utcnow()
        }
        
        if existing:
            # Update existing
            for key, value in analysis_data.items():
                if key != "item_id":  # Don't update FK
                    setattr(existing, key, value)
            await self.analysis_repo.save(existing)
        else:
            # Create new
            from ..models.analysis_result import AnalysisResult
            model = AnalysisResult(**analysis_data)
            await self.analysis_repo.save(model)
    
    async def _cache_image(self, shop_id: str, image_url: str) -> Optional[str]:
        """Cache image locally"""
        try:
            # Generate cache path
            url_hash = hashlib.md5(image_url.encode()).hexdigest()
            cache_dir = Path(self.config.image_cache_dir) / shop_id
            cache_path = cache_dir / f"{url_hash}.jpg"
            
            # Create directory if needed
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Skip if already cached
            if cache_path.exists():
                return str(cache_path)
            
            # Download and cache image (simplified - would use httpx in real implementation)
            # This is a placeholder for actual image downloading logic
            self.logger.info(f"Caching image: {image_url} -> {cache_path}")
            
            # Return relative path for storage
            return str(cache_path)
            
        except Exception as e:
            self.logger.error(f"Failed to cache image {image_url}: {e}")
            return None