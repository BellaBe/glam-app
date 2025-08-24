# services/selfie-service/src/events/listeners.py
from shared.messaging.listener import Listener
from shared.utils.exceptions import ValidationError
from ..schemas.events import RecommendationRequestedPayload
from typing import Dict, Any

class AnalysisCompletedListener(Listener):
    """Listen for analysis completion from AI analyzer"""
    
    @property
    def subject(self) -> str:
        return "evt.ai.analysis.completed.v1"
    
    @property
    def queue_group(self) -> str:
        return "selfie-service-ai-handler"
    
    @property
    def service_name(self) -> str:
        return "selfie-service"
    
    def __init__(self, js_client, service, logger):
        super().__init__(js_client, logger)
        self.service = service
    
    async def on_message(self, data: Dict[str, Any]) -> None:
        """Process AI analysis completion"""
        try:
            # Extract analysis ID and results
            analysis_id = data.get("analysis_id")
            if not analysis_id:
                raise ValidationError("Missing analysis_id")
            
            # Update analysis with AI results
            await self.service.update_with_ai_results(
                analysis_id=analysis_id,
                primary_season=data.get("primary_season"),
                secondary_season=data.get("secondary_season"),
                confidence=data.get("confidence"),
                attributes=data.get("attributes"),
                model_version=data.get("model_version"),
                processing_time=data.get("processing_ms")
            )
            
            self.logger.info(f"Updated analysis {analysis_id} with AI results")
            
        except ValidationError:
            # ACK invalid messages (don't retry)
            self.logger.error("Invalid AI completion event", extra={"data": data})
            return
        except Exception as e:
            # NACK for retry on other errors
            self.logger.error(f"AI completion processing failed: {e}")
            raise
    
    async def on_error(self, error: Exception, data: Dict) -> bool:
        """Error handling with retry logic"""
        if isinstance(error, ValidationError):
            return True  # ACK - don't retry validation errors
        
        # Check retry count
        if self.delivery_count >= self.max_deliver:
            self.logger.error(f"Max retries reached for analysis update")
            return True  # ACK to prevent further retries
        
        return False  # NACK for retry