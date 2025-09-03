# services/merchant-service/src/events/publishers.py

from shared.messaging.events.merchant import MerchantCreatedPayload
from shared.messaging.publisher import Publisher
from shared.messaging.subjects import Subjects


class MerchantEventPublisher(Publisher):
    """Publisher for merchant domain events"""

    @property
    def service_name(self) -> str:
        return "merchant-service"

    async def publish_merchant_created(
        self,
        payload: MerchantCreatedPayload,
        correlation_id: str,
    ) -> str:
        """Publish evt.merchant.installed event"""

        self.logger.info(
            "Publishing merchant installed event",
            extra={"correlation_id": correlation_id, "merchant_id": payload.merchant_id, "domain": payload.domain},
        )

        return await self.publish_event(
            subject=Subjects.MERCHANT_CREATED,
            payload=payload,
            correlation_id=correlation_id,
        )
