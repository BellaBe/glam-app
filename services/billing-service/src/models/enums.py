from enum import Enum

class BillingInterval(str, Enum):
    MONTHLY = "EVERY_30_DAYS"     # Shopify monthly interval
    ANNUAL = "ANNUAL"             # Shopify annual interval
    
class TrialExtensionReason(str, Enum):
    SUPPORT_REQUEST = "support_request"
    TECHNICAL_ISSUE = "technical_issue"
    ONBOARDING_ASSISTANCE = "onboarding_assistance"
    ADMIN_DISCRETION = "admin_discretion"