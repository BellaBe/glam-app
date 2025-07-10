# services/credit-service/src/mappers/credit_account_mapper.py
"""Mapper for credit account model to response schemas."""

from typing import List
from ..models.credit_account import CreditAccount
from ..schemas.credit_account import CreditAccountResponse, CreditAccountSummary


class CreditAccountMapper:
    """Maps between credit account model and response schemas"""
    
    @staticmethod
    def to_response(account: CreditAccount) -> CreditAccountResponse:
        """Convert credit account model to response schema"""
        return CreditAccountResponse(
            id=account.id,
            merchant_id=account.merchant_id,
            balance=account.balance,
            lifetime_credits=account.lifetime_credits,
            last_recharge_at=account.last_recharge_at,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
    
    @staticmethod
    def to_summary(account: CreditAccount) -> CreditAccountSummary:
        """Convert credit account model to summary schema"""
        return CreditAccountSummary(
            merchant_id=account.merchant_id,
            balance=account.balance,
            last_recharge_at=account.last_recharge_at
        )
    
    @staticmethod
    def to_response_list(accounts: List[CreditAccount]) -> List[CreditAccountResponse]:
        """Convert list of credit accounts to response list"""
        return [CreditAccountMapper.to_response(account) for account in accounts]