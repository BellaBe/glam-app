# services/billing-service/src/events/publishers.py
from shared.events import DomainEventPublisher, Streams


class BillingEventPublisher(DomainEventPublisher):
    """Domain-specific event publisher for billing"""
    domain_stream = Streams.BILLING
    service_name_override = "billing-service"