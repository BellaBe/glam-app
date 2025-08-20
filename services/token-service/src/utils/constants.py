# services/token-service/src/utils/constants.py

SUPPORTED_PLATFORMS = {
    "shopify",
    "woocommerce", 
    "bigcommerce",
    "magento",
    "squarespace",
    "custom"
}

TOKEN_TYPES = {
    "oauth",
    "api_key",
    "basic_auth",
    "bearer"
}

# Services allowed to retrieve tokens
ALLOWED_READER_SERVICES = [
    "platform-connector",
    "webhook-service",
    "merchant-service",
    "catalog-service",
    "analytics-service"
]