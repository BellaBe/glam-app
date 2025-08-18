# src/events/types.py
class ConnectorEvents:
    """Connector event type constants"""

    # Incoming events (subscribed)
    SYNC_FETCH_REQUESTED = "sync.fetch.requested.v1"

    # Outgoing events (published)
    SYNC_PRODUCTS_FETCHED = "sync.products.fetched.v1"
    SYNC_FETCH_FAILED = "sync.fetch.failed.v1"
