# services/recommendation-service/src/events/publishers.py
from shared.messaging.publisher import Publisher
from ..schemas.events import MatchCompletedPayload, MatchFailedPayload


class RecommendationEventPublisher(Publisher):
    """Publish recommendation events"""
    
    @property
    def service_name(self) -> str:
        return "recommendation-service"
    
    async def match_completed(
        self,
        payload: MatchCompletedPayload,
        correlation_id: str
    ) -> str:
        """Publish match completed event for credit tracking"""
        return await self.publish_event(
            subject="evt.recommendation.match.completed",
            data=payload.model_dump(mode="json"),
            correlation_id=correlation_id
        )
    
    async def match_failed(
        self,
        payload: MatchFailedPayload,
        correlation_id: str
    ) -> str:
        """Publish match failed event for analytics"""
        return await self.publish_event(
            subject="evt.recommendation.match.failed",
            data=payload.model_dump(mode="json"),
            correlation_id=correlation_id
        )