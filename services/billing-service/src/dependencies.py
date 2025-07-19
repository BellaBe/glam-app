# services/billing-service/src/dependencies.py
from typing import Annotated
from fastapi import Depends, Request
from shared.api import CorrelationIdDep, PaginationDep
from shared.database import DBSessionDep


def get_lifecycle(request: Request) -> 'BillingServiceLifecycle':
    return request.app.state.lifecycle


def get_config(request: Request) -> BillingServiceConfig:
    return request.app.state.config


def get_billing_service(lifecycle: 'BillingServiceLifecycle' = Depends(get_lifecycle)):
    return lifecycle.billing_service


def get_trial_service(lifecycle: 'BillingServiceLifecycle' = Depends(get_lifecycle)):
    return lifecycle.trial_service


def get_purchase_service(lifecycle: 'BillingServiceLifecycle' = Depends(get_lifecycle)):
    return lifecycle.purchase_service


# Type aliases
LifecycleDep = Annotated['BillingServiceLifecycle', Depends(get_lifecycle)]
ConfigDep = Annotated[BillingServiceConfig, Depends(get_config)]
BillingServiceDep = Annotated[BillingService, Depends(get_billing_service)]
TrialServiceDep = Annotated[TrialService, Depends(get_trial_service)]
PurchaseServiceDep = Annotated[OneTimePurchaseService, Depends(get_purchase_service)]