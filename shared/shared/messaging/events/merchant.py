# shared/messaging/events/merchant.py
from datetime import datetime
from typing import Literal

from pydantic import Field

from shared.messaging.events.base import BaseEventPayload

MerchantStatus = Literal["PENDING", "ACTIVE", "PAUSED", "SUSPENDED", "UNINSTALLED"]


class _MerchantSnapshotMixin(BaseEventPayload):
    # Profile (synced)
    name: str
    email: str
    primary_domain: str | None
    currency: str
    country: str
    platform_version: str | None
    scopes: str

    # State + watermarks
    status: MerchantStatus
    last_synced_at: datetime | None

    # Audit
    created_at: datetime
    updated_at: datetime


class MerchantCreatedPayload(BaseEventPayload):
    """Emitted after first persistence of a merchant record."""

    name: str
    email: str
    primary_domain: str | None
    currency: str
    country: str
    platform_version: str | None
    scopes: str


class MerchantSyncedPayload(BaseEventPayload):
    """Emitted on each sync (create or update)."""

    name: str
    email: str
    primary_domain: str | None
    currency: str
    country: str
    platform_version: str | None
    scopes: str

    # State + watermarks
    status: MerchantStatus
    last_synced_at: datetime | None


class MerchantReinstalledPayload(_MerchantSnapshotMixin):
    """Emitted when a previously uninstalled merchant reinstalls the app."""

    # (status should be PENDING at this time; consumers see it directly)


class MerchantUninstalledPayload(BaseEventPayload):
    """Emitted when app is uninstalled for a merchant."""

    # Minimal by design: identifiers + updated status is observable
    # Optionally include these for convenience:
    status: MerchantStatus = Field(default="UNINSTALLED")
    updated_at: datetime  # when the row was updated


class MerchantStatusChangedPayload(_MerchantSnapshotMixin):
    """Emitted when merchant.status transitions due to internal logic."""

    from_status: MerchantStatus
    to_status: MerchantStatus
