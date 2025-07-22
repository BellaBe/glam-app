# services/merchant-service/src/models/enums.py
from enum import Enum

class MerchantStatusEnum(str, Enum):
    """Status enum for Merchant"""
    # Initial States
    PENDING = "PENDING"           # App installed, awaiting setup
    ONBOARDING = "ONBOARDING"     # Going through setup process
    # Active States  
    TRIAL = "TRIAL"               # In trial period
    ACTIVE = "ACTIVE"             # Paid subscription active
    # Inactive States
    SUSPENDED = "SUSPENDED"       # Temporarily disabled
    DEACTIVATED = "DEACTIVATED"   # App uninstalled or permanently disabled
