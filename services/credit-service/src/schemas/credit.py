from __future__ import annotations
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

CreditOperation = Literal["credit", "debit"]
CreditSource = Literal["trial", "purchase", "refund"]


class CreditBalanceOut(BaseModel):
    """Public API response for credit balance"""
    balance: int
    trial_credits: int
    purchased_credits: int
    total_granted: int
    total_consumed: int
    platform_name: str
    platform_domain: str


class CreditAccountOut(BaseModel):
    """Internal representation of credit account"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    merchant_id: UUID
    platform_name: str
    platform_id: str
    platform_domain: str
    trial_credits: int
    purchased_credits: int
    balance: int
    total_granted: int
    total_consumed: int
    trial_credits_used: int
    created_at: datetime
    updated_at: datetime


class CreditTransactionOut(BaseModel):
    """Internal representation of credit transaction"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    merchant_id: UUID
    amount: int
    operation: CreditOperation
    source: CreditSource
    balance_before: int
    balance_after: int
    trial_before: int | None
    trial_after: int | None
    purchased_before: int | None
    purchased_after: int | None
    reference_type: str
    reference_id: str
    metadata: dict | None
    created_at: datetime


# Event payload schemas
class BillingRecordCreatedPayload(BaseModel):
    merchant_id: UUID
    platform_name: str
    platform_id: str
    platform_domain: str


class TrialActivatedPayload(BaseModel):
    merchant_id: UUID
    grant_amount: int = 500


class PurchaseCompletedPayload(BaseModel):
    merchant_id: UUID
    payment_id: str
    product_id: str
    metadata: dict


class PurchaseRefundedPayload(BaseModel):
    merchant_id: UUID
    payment_id: str
    metadata: dict


class MatchCompletedPayload(BaseModel):
    merchant_id: UUID
    match_id: str
    shopper_id: str
    matched_items_count: int