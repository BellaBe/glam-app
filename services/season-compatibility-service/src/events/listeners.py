# services/season-compatibility/src/events/listeners.py
from shared.messaging.listener import Listener
from shared.utils.exceptions import ValidationError

from ..schemas.events import (
    AIAnalysisCompletedPayload,
    ComputationMetadata,
    SeasonComputationCompletedPayload,
    TopSeasons,
)


class AIAnalysisCompletedListener(Listener):
    """Listen for AI analysis completion events"""

    @property
    def subject(self) -> str:
        return "evt.catalog.ai.analysis.completed.v1"

    @property
    def queue_group(self) -> str:
        return "season-compatibility-ai-handler"

    @property
    def service_name(self) -> str:
        return "season-compatibility"

    def __init__(self, js_client, publisher, service, logger):
        super().__init__(js_client, logger)
        self.publisher = publisher
        self.service = service

    async def on_message(self, data: dict) -> None:
        """Process AI analysis completed event"""
        try:
            # Validate payload
            payload = AIAnalysisCompletedPayload(**data)
            correlation_id = data.get("correlation_id", "unknown")

            # Process with service
            result = await self.service.process_ai_analysis(payload=payload, correlation_id=correlation_id)

            # Prepare event payload
            event_payload = SeasonComputationCompletedPayload(
                item_id=payload.item_id,
                merchant_id=payload.merchant_id,
                product_id=payload.product_id,
                variant_id=payload.variant_id,
                correlation_id=correlation_id,
                season_scores=result["scores"],
                top_seasons=TopSeasons(
                    primary=result["result"].primary_season,
                    secondary=result["result"].secondary_season,
                    tertiary=result["result"].tertiary_season,
                ),
                max_score=result["result"].max_score,
                computation_metadata=ComputationMetadata(
                    colors_analyzed=len(payload.precise_colors.rgb_values),
                    attributes_used=list(payload.attributes.model_dump().keys()),
                    computation_time_ms=result["computation_time_ms"],
                ),
            )

            # Publish success event
            await self.publisher.season_computation_completed(payload=event_payload, correlation_id=correlation_id)

        except ValidationError as e:
            # ACK invalid messages (don't retry)
            self.logger.error(f"Invalid AI analysis event: {e}", extra={"data": data})
            return

        except Exception as e:
            # NACK for retry on other errors
            self.logger.error(f"AI analysis processing failed: {e}")
            # Publish failure event
            await self.publisher.season_computation_failed(
                item_id=data.get("item_id", "unknown"),
                error=str(e),
                retry_count=1,
                correlation_id=data.get("correlation_id", "unknown"),
            )
            raise

    async def on_error(self, error: Exception, data: dict) -> bool:
        """Error handling with retry logic"""
        if isinstance(error, ValidationError):
            return True  # ACK - don't retry validation errors
        return False  # NACK for retry
