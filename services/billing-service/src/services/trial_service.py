# services/billing-service/src/services/trial_service.py
class TrialService:
    """Service for managing trial periods and extensions"""
    
    def __init__(
        self,
        extension_repo: TrialExtensionRepository,
        event_publisher: 'BillingEventPublisher',
        logger: ServiceLogger,
        config: BillingServiceConfig
    ):
        self.extension_repo = extension_repo
        self.event_publisher = event_publisher
        self.logger = logger
        self.config = config
    
    async def get_trial_status(
        self, 
        merchant_id: UUID, 
        merchant_created_at: datetime
    ) -> TrialStatusResponse:
        """Get comprehensive trial status for merchant"""
        
        # Calculate trial dates using provided merchant creation date
        trial_start = merchant_created_at
        trial_end = trial_start + timedelta(days=self.config.trial_period_days)
        
        # Apply any extensions
        extensions = await self.extension_repo.find_by_merchant_id(merchant_id)
        total_extension_days = sum(ext.days_added for ext in extensions)
        trial_end += timedelta(days=total_extension_days)
        
        # Calculate remaining days
        now = datetime.utcnow()
        days_remaining = max(0, (trial_end - now).days)
        is_active = days_remaining > 0
        
        return TrialStatusResponse(
            merchant_id=merchant_id,
            is_trial_active=is_active,
            trial_start_date=trial_start,
            trial_end_date=trial_end,
            days_remaining=days_remaining,
            total_extensions=len(extensions),
            total_extension_days=total_extension_days
        )
    
    async def extend_trial(
        self,
        merchant_id: UUID,
        additional_days: int,
        reason: TrialExtensionReason,
        extended_by: str,
        current_trial_end: datetime,
        correlation_id: str = None
    ) -> TrialExtensionResponse:
        """Extend trial period for merchant"""
        
        if additional_days < 1 or additional_days > self.config.max_extension_days:
            raise BillingError(f"Extension must be between 1-{self.config.max_extension_days} days")
        
        # Check extension limits
        existing_extensions = await self.extension_repo.count_by_merchant_id(merchant_id)
        if existing_extensions >= self.config.max_trial_extensions:
            raise BillingError("Maximum trial extensions reached")
        
        # Create extension record
        extension = TrialExtension(
            merchant_id=merchant_id,
            days_added=additional_days,
            reason=reason.value,
            extended_by=extended_by,
            original_trial_end=current_trial_end,
            new_trial_end=current_trial_end + timedelta(days=additional_days)
        )
        
        await self.extension_repo.save(extension)
        
        # Publish extension event
        await self.event_publisher.publish_event(
            "evt.billing.trial.extended",
            payload={
                "merchant_id": str(merchant_id),
                "extension_id": str(extension.id),
                "days_added": additional_days,
                "new_trial_end": extension.new_trial_end.isoformat(),
                "reason": reason.value,
                "extended_by": extended_by
            },
            correlation_id=correlation_id
        )
        
        return TrialExtensionResponse(
            success=True,
            extension_id=extension.id,
            new_trial_end_date=extension.new_trial_end,
            total_trial_days=(extension.new_trial_end - current_trial_end).days + self.config.trial_period_days
        )