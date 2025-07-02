from enum import Enum

class NotificationType(str, Enum):
    """Notification type constants"""
    # System notifications
    WELCOME = "welcome"
    REGISTRATION_FINISH = "registration_finish"
    REGISTRATION_SYNC = "registration_sync"
    
    # Billing notifications
    BILLING_EXPIRED = "billing_expired"
    BILLING_CHANGED = "billing_changed"
    BILLING_LOW_CREDITS = "billing_low_credits"
    BILLING_ZERO_BALANCE = "billing_zero_balance"
    BILLING_DEACTIVATED = "billing_deactivated"
    
    # Custom notifications
    MARKETING = "marketing"
    ANNOUNCEMENT = "announcement"
    CUSTOM = "custom"

# Default templates for each type
DEFAULT_TEMPLATES = {
    NotificationType.WELCOME: {
        "subject": "Welcome to GlamYouUp, {{ shop_name }}!",
        "required_vars": ["shop_name"],
        "optional_vars": ["features", "product_count"]
    },
    NotificationType.REGISTRATION_FINISH: {
        "subject": "Product Registration Complete - {{ product_count }} products registered",
        "required_vars": ["product_count"],
        "optional_vars": []
    },
    NotificationType.REGISTRATION_SYNC: {
        "subject": "Product Sync Results",
        "required_vars": ["added_count", "updated_count"],
        "optional_vars": ["removed_count"]
    },
    NotificationType.BILLING_EXPIRED: {
        "subject": "Your {{ plan_name }} subscription has expired",
        "required_vars": ["plan_name", "renewal_link"],
        "optional_vars": []
    },
    NotificationType.BILLING_CHANGED: {
        "subject": "Plan changed to {{ plan_name }}",
        "required_vars": ["plan_name"],
        "optional_vars": ["previous_plan"]
    },
    NotificationType.BILLING_LOW_CREDITS: {
        "subject": "Low credit balance warning",
        "required_vars": ["current_balance", "days_remaining", "expected_depletion_date", "billing_link"],
        "optional_vars": []
    },
    NotificationType.BILLING_ZERO_BALANCE: {
        "subject": "Zero balance - Features will be deactivated",
        "required_vars": ["deactivation_time", "billing_link"],
        "optional_vars": []
    },
    NotificationType.BILLING_DEACTIVATED: {
        "subject": "Features deactivated due to {{ reason }}",
        "required_vars": ["reason", "reactivation_link"],
        "optional_vars": []
    }
}

# Rate limits per notification type
TYPE_RATE_LIMITS = {
    NotificationType.BILLING_LOW_CREDITS: {"total_limit": 5},
    NotificationType.BILLING_ZERO_BALANCE: {"total_limit": 2},
    NotificationType.BILLING_DEACTIVATED: {"total_limit": 7}
}