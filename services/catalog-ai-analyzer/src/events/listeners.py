# services/catalog-ai-analyzer/src/events/listeners.py
import time
from shared.messaging.listener import Listener
from shared.utils.exceptions import ValidationError
from ..schemas.events import CatalogAnalysisRequestedPayload

class CatalogAnalysisRequestedListener(Listener):
    """Listen for catalog analysis requests"""
    
    @property
    def subject(self) -> str:
        return "evt.catalog.ai.analysis.requested"
    
    @property
    def queue_group(self) -> str:
        return "catalog-ai-analyzer-requests"
    
    @property
    def service_name(self) -> str:
        return "catalog-ai-analyzer"
    
    def __init__(self, js_client, publisher, service, logger):
        super().__init__(js_client, logger)
        self.publisher = publisher
        self.service = service
    
    async def on_message(self, data: dict) -> None:
        """Process catalog analysis request"""
        start_time = time.perf_counter()
        
        try:
            # Validate and parse payload
            payload = CatalogAnalysisRequestedPayload(**data)
            
            self.logger.info(
                f"Processing analysis request for merchant {payload.merchant_id}, "
                f"sync {payload.sync_id}, {len(payload.items)} items"
            )
            
            # Process batch
            processed, failed, partial = await self.service.analyze_batch(
                merchant_id=payload.merchant_id,
                sync_id=payload.sync_id,
                correlation_id=payload.correlation_id,
                items=payload.items
            )
            
            # Publish batch completion
            total_time_ms = int((time.perf_counter() - start_time) * 1000)
            
            await self.publisher.batch_completed(
                payload={
                    "merchant_id": payload.merchant_id,
                    "sync_id": payload.sync_id,
                    "correlation_id": payload.correlation_id,
                    "processed": processed,
                    "failed": failed,
                    "partial": partial,
                    "total_time_ms": total_time_ms
                },
                correlation_id=payload.correlation_id
            )
            
            self.logger.info(
                f"Batch completed: {processed} processed, {failed} failed, "
                f"{partial} partial in {total_time_ms}ms"
            )
            
        except ValidationError as e:
            self.logger.error(f"Invalid analysis request: {e}")
            # ACK invalid messages (don't retry)
            return
        except Exception as e:
            self.logger.error(f"Analysis request processing failed: {e}", exc_info=True)
            raise  # NACK for retry
    
    async def on_error(self, error: Exception, data: dict) -> bool:
        """Handle processing errors"""
        if isinstance(error, ValidationError):
            return True  # ACK validation errors
        
        # Check retry count
        if self.delivery_count >= self.max_deliver:
            self.logger.error(f"Max retries exceeded, dropping message")
            # Could send to DLQ here
            return True
        
        return False  # NACK for retry