from shared.events import DomainEventPublisher, Streams

class AnalyticsEventPublisher(DomainEventPublisher):
    """Analytics domain event publisher"""
    domain_stream = Streams.ANALYTICS
    service_name_override = "analytics-service"


