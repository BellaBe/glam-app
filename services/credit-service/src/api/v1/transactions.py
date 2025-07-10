# services/credit-service/src/api/v1/transactions.py
"""Credit transaction API endpoints."""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Query

from shared.api.responses import success_response, paginated_response
from shared.api.pagination import PaginationParams, apply_pagination_params

from ...dependencies import (
    CreditTransactionRepoDep, 
    CreditTransactionMapperDep
)
from ...schemas.credit_transaction import (
    CreditTransactionResponse, 
    CreditTransactionFilter
)
from ...models.credit_transaction import TransactionType, ReferenceType

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("")
async def get_transactions(
    merchant_id: Optional[UUID] = Query(None),
    transaction_type: Optional[TransactionType] = Query(None),
    reference_type: Optional[ReferenceType] = Query(None),
    pagination: PaginationParams = Depends(apply_pagination_params),
    transaction_repo: CreditTransactionRepoDep,
    transaction_mapper: CreditTransactionMapperDep
):
    """Get credit transactions with pagination and filtering"""
    
    if merchant_id:
        transactions, total = await transaction_repo.get_merchant_transactions(
            merchant_id=merchant_id,
            pagination=pagination,
            transaction_type=transaction_type,
            reference_type=reference_type
        )
    else:
        # This would require additional repository method for admin access
        raise HTTPException(400, "merchant_id is required")
    
    response_data = transaction_mapper.to_response_list(transactions)
    
    return paginated_response(
        data=response_data,
        page=pagination.page,
        limit=pagination.limit,
        total=total,
        base_url="/api/v1/credits/transactions"
    )


@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: UUID,
    transaction_repo: CreditTransactionRepoDep,
    transaction_mapper: CreditTransactionMapperDep
) -> CreditTransactionResponse:
    """Get specific credit transaction"""
    
    transaction = await transaction_repo.get_by_id(transaction_id)
    
    if not transaction:
        raise HTTPException(404, "Transaction not found")
    
    return success_response(transaction_mapper.to_response(transaction))