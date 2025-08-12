from enum import Enum

class WebhookPlatform(str, Enum):
    SHOPIFY = "shopify"

class WebhookStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

class ShopifyWebhookTopic(str, Enum):
    """
    Canonical Shopify topics. Enum values are the *raw* Shopify topic strings.
    This lets us avoid a separate mapping.
    """
    APP_UNINSTALLED                = "app/uninstalled"
    APP_SUBSCRIPTIONS_UPDATE       = "app_subscriptions/update"
    APP_PURCHASES_ONE_TIME_UPDATE  = "app_purchases_one_time/update"
    ORDERS_CREATE                  = "orders/create"
    PRODUCTS_CREATE                = "products/create"
    PRODUCTS_UPDATE                = "products/update"
    PRODUCTS_DELETE                = "products/delete"
    COLLECTIONS_CREATE             = "collections/create"
    COLLECTIONS_UPDATE             = "collections/update"
    COLLECTIONS_DELETE             = "collections/delete"
    INVENTORY_LEVELS_UPDATE        = "inventory_levels/update"
    CUSTOMERS_DATA_REQUEST         = "customers/data_request"
    CUSTOMERS_REDACT               = "customers/redact"
    SHOP_REDACT                    = "shop/redact"
    UNKNOWN                        = "__unknown__"

def parse_topic(raw: str) -> ShopifyWebhookTopic:
    """
    Convert raw header string → Enum. Unknown → ShopifyWebhookTopic.UNKNOWN.
    """
    try:
        return ShopifyWebhookTopic(raw)
    except ValueError:
        return ShopifyWebhookTopic.UNKNOWN
