# services/season-compatibility/src/events/publishers.py
from shared.messaging.publisher import Publisher

from ..schemas.events import SeasonComputationCompletedPayload


class SeasonEventPublisher(Publisher):
    """Publish season computation events"""

    @property
    def service_name(self) -> str:
        return "season-compatibility"

    async def season_computation_completed(
        self, payload: SeasonComputationCompletedPayload, correlation_id: str
    ) -> str:
        """Publish season computation completed event"""
        return await self.publish_event(
            subject="evt.season.computation.completed.v1", data=payload.model_dump(), correlation_id=correlation_id
        )

    async def season_computation_failed(self, item_id: str, error: str, retry_count: int, correlation_id: str) -> str:
        """Publish season computation failed event"""
        return await self.publish_event(
            subject="evt.season.computation.failed.v1",
            data={"item_id": item_id, "error": error, "retry_count": retry_count},
            correlation_id=correlation_id,
        )
