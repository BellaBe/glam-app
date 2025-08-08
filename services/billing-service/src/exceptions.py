from shared.utils.exceptions import (
    DomainError, 
    ValidationError, 
    NotFoundError, 
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
    InfrastructureError,
    ServiceUnavailableError
)

class BillingError(DomainError):
    """Base class for billing domain errors"""
    pass

class InvalidDomainError(ValidationError):
    """Invalid shop domain format"""
    def __init__(self, domain: str):
        super().__init__(
            message=f"Invalid shop domain format: {domain}",
            field="shop_domain",
            value=domain
        )

class InvalidPlanError(ValidationError):
    """Invalid plan ID"""
    def __init__(self, plan_id: str):
        super().__init__(
            message=f"Invalid plan ID: {plan_id}",
            field="plan",
            value=plan_id
        )

class InvalidReturnUrlError(ValidationError):
    """Invalid return URL"""
    def __init__(self, url: str):
        super().__init__(
            message="Invalid return URL",
            field="return_url",
            value=url
        )

class MissingHeaderError(ValidationError):
    """Missing required header"""
    def __init__(self, header: str):
        super().__init__(
            message=f"Missing required header: {header}",
            field="headers",
            value=header
        )

class TrialAlreadyUsedError(ConflictError):
    """Trial has already been used"""
    def __init__(self, shop_domain: str):
        super().__init__(
            message="Trial has already been used for this merchant",
            conflicting_resource="trial",
            current_state="consumed"
        )

class SubscriptionExistsError(ConflictError):
    """Already subscribed to this plan"""
    def __init__(self, plan_id: str):
        super().__init__(
            message="Already subscribed to this plan",
            conflicting_resource="subscription",
            current_state=plan_id
        )

class PolicyBlockedError(ForbiddenError):
    """Trial creation blocked by policy"""
    def __init__(self, reason: str = "Trial creation blocked by policy"):
        super().__init__(
            message=reason,
            required_permission="trial_creation"
        )

class TokenServiceError(ServiceUnavailableError):
    """Failed to fetch access token"""
    def __init__(self):
        super().__init__(
            message="Failed to fetch access token",
            service="token-service",
            retryable=True
        )

class ShopifyApiError(ServiceUnavailableError):
    """Shopify API error"""
    def __init__(self, details: str):
        super().__init__(
            message=f"Shopify API error: {details}",
            service="shopify",
            retryable=True
        )

