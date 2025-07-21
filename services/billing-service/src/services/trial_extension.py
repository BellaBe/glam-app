# services/billing-service/src/services/trial_extension.py
"""Business logic for trial extensions."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from shared.utils.logger import ServiceLogger

from ..config import BillingServiceConfig
from ..events import BillingEventPublisher
from ..exceptions import ConflictError
from ..models import TrialExtension, TrialExtensionReason
from ..repositories import TrialExtensionRepository
from ..mappers.trial_extension import TrialExtensionMapper
from ..schemas.trial_extension import TrialStatusOut, TrialExtensionOut


class TrialService:
    """Business logic for trials & extensions."""

    def __init__(
        self,
        extension_repo: TrialExtensionRepository,
        extension_mapper: TrialExtensionMapper,
        event_publisher: BillingEventPublisher,
        logger: ServiceLogger,
        config: BillingServiceConfig,
    ):
        self.extension_repo = extension_repo
        self.extension_mapper = extension_mapper
        self.event_publisher = event_publisher
        self.logger = logger
        self.config = config

    async def _compute_trial_window(self, merchant_id: UUID) -> tuple[datetime, datetime, int]:
        """
        Returns (trial_start, trial_end, total_extension_days).
        Uses the earliest extension record as anchor; if none exists,
        assumes the trial started exactly `trial_period_days` ago.
        """
        extensions = await self.extension_repo.find_by_merchant_id(merchant_id)

        if extensions:
            earliest_original_end = min(e.original_trial_end for e in extensions)
            trial_start = earliest_original_end - timedelta(days=self.config.trial_period_days)
            total_ext_days = sum(e.days_added for e in extensions)
        else:
            trial_start = datetime.now(timezone.utc) - timedelta(days=self.config.trial_period_days)
            total_ext_days = 0

        trial_end = trial_start + timedelta(
            days=self.config.trial_period_days + total_ext_days
        )
        return trial_start, trial_end, total_ext_days

    async def get_trial_status(self, merchant_id: UUID) -> TrialStatusOut:
        trial_start, trial_end, total_ext_days = await self._compute_trial_window(
            merchant_id
        )
        now = datetime.now(timezone.utc)
        days_remaining = max(0, (trial_end - now).days)

        return TrialStatusOut(
            merchant_id=merchant_id,
            is_trial_active=days_remaining > 0,
            trial_start_date=trial_start,
            trial_end_date=trial_end,
            days_remaining=days_remaining,
            total_extensions=await self.extension_repo.count_by_merchant_id(
                merchant_id
            ),
            total_extension_days=total_ext_days,
        )

    async def extend_trial(
        self,
        merchant_id: UUID,
        additional_days: int,
        reason: TrialExtensionReason,
        extended_by: str,
    ) -> TrialExtensionOut:
        if not (1 <= additional_days <= self.config.max_extension_days):
            raise ConflictError(
                f"Extension must be between 1‑{self.config.max_extension_days} days"
            )

        if (
            await self.extension_repo.count_by_merchant_id(merchant_id)
            >= self.config.max_trial_extensions
        ):
            raise ConflictError("Maximum trial extensions reached")

        # Current end = existing max(new_trial_end) OR nominal end of base window
        latest = await self.extension_repo.latest_trial_end(merchant_id)
        if latest is None:
            # base window ends trial_period_days after assumed start
            latest = (datetime.now(timezone.utc) - timedelta(days=self.config.trial_period_days)) + timedelta(
                days=self.config.trial_period_days
            )

        extension = TrialExtension(
            merchant_id=merchant_id,
            days_added=additional_days,
            reason=reason,
            extended_by=extended_by,
            original_trial_end=latest,
            new_trial_end=latest + timedelta(days=additional_days),
        )
        await self.extension_repo.save(extension)

        await self.event_publisher.publish_event(
            "evt.billing.trial.extended",
            payload={
                "merchant_id": str(merchant_id),
                "extension_id": str(extension.id),
                "days_added": additional_days,
                "new_trial_end": extension.new_trial_end.isoformat(),
                "reason": reason.value,
                "extended_by": extended_by,
            },
        )

        return self.extension_mapper.to_out(extension)
