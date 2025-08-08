from shared.utils.exceptions import (
    GlamBaseError,
    ValidationError,
    UnauthorizedError,
)


class WebhookError(GlamBaseError):
    """Base class for webhook errors"""
    pass


class InvalidContentTypeError(ValidationError):
    """Invalid content type for webhook"""
    def __init__(self, content_type: str):
        super().__init__(
            message="Content-Type must be application/json",
            field="content-type",
            value=content_type
        )


class PayloadTooLargeError(ValidationError):
    """Webhook payload exceeds size limit"""
    def __init__(self, size: int, limit: int):
        super().__init__(
            message=f"Request payload exceeds {limit} byte limit",
            field="payload",
            value=f"{size} bytes"
        )


class InvalidSignatureError(UnauthorizedError):
    """Invalid HMAC signature"""
    def __init__(self):
        super().__init__(
            message="Invalid HMAC signature",
            auth_type="hmac"
        )


class MissingHeadersError(ValidationError):
    """Required headers missing"""
    def __init__(self, missing_headers: list):
        super().__init__(
            message=f"Required headers missing: {', '.join(missing_headers)}",
            field="headers",
            value=missing_headers
        )


class DomainMismatchError(ValidationError):
    """Shop domain mismatch"""
    def __init__(self, header_domain: str, payload_domain: str):
        super().__init__(
            message="Shop domain mismatch",
            field="shop_domain",
            value=f"header: {header_domain}, payload: {payload_domain}"
        )


class MalformedPayloadError(ValidationError):
    """Invalid JSON payload"""
    def __init__(self):
        super().__init__(
            message="Invalid JSON payload",
            field="payload"
        )


class InvalidShopDomainError(ValidationError):
    """Invalid shop domain format"""
    def __init__(self, domain: str):
        super().__init__(
            message="Invalid shop domain - must end with .myshopify.com",
            field="shop_domain",
            value=domain
        )


class IPNotAllowedError(UnauthorizedError):
    """IP not in allowlist"""
    def __init__(self, ip: str):
        super().__init__(
            message="IP not in allowlist",
            auth_type="ip_allowlist"
        )


