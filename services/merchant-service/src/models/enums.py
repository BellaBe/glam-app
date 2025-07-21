from enum import StrEnum


class MerchantStatusEnum(StrEnum):
    PENDING = "PENDING"
    ONBOARDING = "ONBOARDING"
    TRIAL = "TRIAL"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"