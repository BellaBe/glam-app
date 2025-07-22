# src/events/subscribers.py
from shared.events import DomainEventSubscriber
from typing import Dict, Any
import json

class ProductsFetchedSubscriber(DomainEventSubscriber):
    """Subscribe to products fetched events from platform connector"""
    stream_name = "CATALOG"
    subject = "sync.products.fetched.v1"
    event_type = "sync.products.fetched.v1"
    durable_name = "catalog-products-fetched"
    
    async def on_event(self, event: dict, headers: dict):
        """Process products fetched event"""
        service = self.get_dependency("catalog_service")
        logger = self.get_dependency("logger")
        
        payload = event["payload"]
        correlation_id = event.get("correlation_id")
        
        logger.info(
            "Processing products fetched event",
            extra={
                "event_type": self.event_type,
                "sync_id": payload.get("sync_id"),
                "shop_id": payload.get("shop_id"),
                "batch_number": payload.get("batch_number"),
                "correlation_id": correlation_id
            }
        )
        
        await service.process_products_batch(payload, correlation_id)

class AnalysisCompletedSubscriber(DomainEventSubscriber):
    """Subscribe to analysis completed events"""
    stream_name = "CATALOG"
    subject = "analysis.completed.v1"
    event_type = "analysis.completed.v1"
    durable_name = "catalog-analysis-completed"
    
    async def on_event(self, event: dict, headers: dict):
        """Process analysis completed event"""
        service = self.get_dependency("catalog_service")
        logger = self.get_dependency("logger")
        
        payload = event["payload"]
        correlation_id = event.get("correlation_id")
        
        logger.info(
            "Processing analysis completed event",
            extra={
                "event_type": self.event_type,
                "sync_id": payload.get("sync_id"),
                "shop_id": payload.get("shop_id"),
                "batch_id": payload.get("batch_id"),
                "results_count": len(payload.get("results", [])),
                "correlation_id": correlation_id
            }
        )
        
        await service.process_analysis_results(payload, correlation_id)
