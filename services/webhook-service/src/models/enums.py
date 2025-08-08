from enum import Enum


class WebhookPlatform(str, Enum):
    SHOPIFY = "shopify"


class WebhookStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class ShopifyWebhookTopic(str, Enum):
    """Normalized Shopify webhook topics"""
    APP_UNINSTALLED = "APP_UNINSTALLED"
    APP_SUBSCRIPTIONS_UPDATE = "APP_SUBSCRIPTIONS_UPDATE"
    APP_PURCHASES_ONE_TIME_UPDATE = "APP_PURCHASES_ONE_TIME_UPDATE"
    ORDERS_CREATE = "ORDERS_CREATE"
    PRODUCTS_CREATE = "PRODUCTS_CREATE"
    PRODUCTS_UPDATE = "PRODUCTS_UPDATE"
    PRODUCTS_DELETE = "PRODUCTS_DELETE"
    COLLECTIONS_CREATE = "COLLECTIONS_CREATE"
    COLLECTIONS_UPDATE = "COLLECTIONS_UPDATE"
    COLLECTIONS_DELETE = "COLLECTIONS_DELETE"
    INVENTORY_LEVELS_UPDATE = "INVENTORY_LEVELS_UPDATE"
    CUSTOMERS_DATA_REQUEST = "CUSTOMERS_DATA_REQUEST"
    CUSTOMERS_REDACT = "CUSTOMERS_REDACT"
    SHOP_REDACT = "SHOP_REDACT"
    UNKNOWN = "UNKNOWN"


# Topic mapping from raw to enum
TOPIC_MAPPING = {
    'app/uninstalled': ShopifyWebhookTopic.APP_UNINSTALLED,
    'app_subscriptions/update': ShopifyWebhookTopic.APP_SUBSCRIPTIONS_UPDATE,
    'app_purchases_one_time/update': ShopifyWebhookTopic.APP_PURCHASES_ONE_TIME_UPDATE,
    'orders/create': ShopifyWebhookTopic.ORDERS_CREATE,
    'products/create': ShopifyWebhookTopic.PRODUCTS_CREATE,
    'products/update': ShopifyWebhookTopic.PRODUCTS_UPDATE,
    'products/delete': ShopifyWebhookTopic.PRODUCTS_DELETE,
    'collections/create': ShopifyWebhookTopic.COLLECTIONS_CREATE,
    'collections/update': ShopifyWebhookTopic.COLLECTIONS_UPDATE,
    'collections/delete': ShopifyWebhookTopic.COLLECTIONS_DELETE,
    'inventory_levels/update': ShopifyWebhookTopic.INVENTORY_LEVELS_UPDATE,
    'customers/data_request': ShopifyWebhookTopic.CUSTOMERS_DATA_REQUEST,
    'customers/redact': ShopifyWebhookTopic.CUSTOMERS_REDACT,
    'shop/redact': ShopifyWebhookTopic.SHOP_REDACT,
}


def normalize_topic_enum(raw_topic: str) -> str:
    """Convert raw topic to normalized enum value"""
    topic = TOPIC_MAPPING.get(raw_topic, ShopifyWebhookTopic.UNKNOWN)
    if topic == ShopifyWebhookTopic.UNKNOWN:
        # For unknown topics, create a dynamic enum-like value
        return f"UNKNOWN_{raw_topic.upper().replace('/', '_')}"
    return topic.value


