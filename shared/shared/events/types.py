# Remove this once full per domain split is implemented

class Commands:
    """All commands in the system (cmd.*)"""
    
    # Merchant Commands
    MERCHANT_ONBOARD = "cmd.merchant.onboard"
    MERCHANT_UPDATE_PROFILE = "cmd.merchant.update_profile"
    MERCHANT_VERIFY = "cmd.merchant.verify"
    MERCHANT_SUSPEND = "cmd.merchant.suspend"
    MERCHANT_ACTIVATE = "cmd.merchant.activate"
    
    # Billing Commands
    BILLING_CREATE_INVOICE = "cmd.billing.create_invoice"
    BILLING_PROCESS_PAYMENT = "cmd.billing.process_payment"
    BILLING_ISSUE_REFUND = "cmd.billing.issue_refund"
    BILLING_CALCULATE_COMMISSION = "cmd.billing.calculate_commission"
    
    # Credit Commands
    CREDIT_CHECK_ELIGIBILITY = "cmd.credit.check_eligibility"
    CREDIT_APPROVE_LIMIT = "cmd.credit.approve_limit"
    CREDIT_PROCESS_APPLICATION = "cmd.credit.process_application"
    CREDIT_UPDATE_SCORE = "cmd.credit.update_score"
    
    # Auth Commands
    AUTH_CREATE_USER = "cmd.auth.create_user"
    AUTH_VERIFY_EMAIL = "cmd.auth.verify_email"
    AUTH_RESET_PASSWORD = "cmd.auth.reset_password"
    AUTH_REVOKE_TOKENS = "cmd.auth.revoke_tokens"
    
    # Profile Commands
    PROFILE_CREATE = "cmd.profile.create"
    PROFILE_UPDATE = "cmd.profile.update"
    PROFILE_VERIFY_SELFIE = "cmd.profile.verify_selfie"
    PROFILE_ANALYZE_BEHAVIOR = "cmd.profile.analyze_behavior"
    
    # Analytics Commands
    ANALYTICS_TRACK_EVENT = "cmd.analytics.track_event"
    ANALYTICS_GENERATE_REPORT = "cmd.analytics.generate_report"
    ANALYTICS_EXPORT_DATA = "cmd.analytics.export_data"
    
    # Scheduler Commands
    SCHEDULER_CREATE_JOB = "cmd.scheduler.create_job"
    SCHEDULER_CANCEL_JOB = "cmd.scheduler.cancel_job"
    SCHEDULER_UPDATE_JOB = "cmd.scheduler.update_job"
    
    # Webhook Commands
    WEBHOOK_REGISTER = "cmd.webhook.register"
    WEBHOOK_DELIVER = "cmd.webhook.deliver"
    WEBHOOK_RETRY = "cmd.webhook.retry"


class Events:
    """All events in the system (evt.*)"""
    
    # Job Events (from catalog-job-processor)
    JOB_CREATED = "evt.job.created"
    JOB_STARTED = "evt.job.started"
    JOB_PROGRESS_UPDATED = "evt.job.progress.updated"
    JOB_COMPLETED = "evt.job.completed"
    JOB_FAILED = "evt.job.failed"
    JOB_RETRY_SCHEDULED = "evt.job.retry.scheduled"
    
    # Merchant Events
    MERCHANT_ONBOARDED = "evt.merchant.onboarded"
    MERCHANT_VERIFIED = "evt.merchant.verified"
    MERCHANT_PROFILE_UPDATED = "evt.merchant.profile.updated"
    MERCHANT_SUSPENDED = "evt.merchant.suspended"
    MERCHANT_ACTIVATED = "evt.merchant.activated"
    MERCHANT_TIER_CHANGED = "evt.merchant.tier.changed"
    
    # Billing Events
    BILLING_INVOICE_CREATED = "evt.billing.invoice.created"
    BILLING_PAYMENT_PROCESSED = "evt.billing.payment.processed"
    BILLING_PAYMENT_FAILED = "evt.billing.payment.failed"
    BILLING_REFUND_ISSUED = "evt.billing.refund.issued"
    BILLING_COMMISSION_CALCULATED = "evt.billing.commission.calculated"
    BILLING_SUBSCRIPTION_UPDATED = "evt.billing.subscription.updated"
    
    # Credit Events
    CREDIT_ELIGIBILITY_CHECKED = "evt.credit.eligibility.checked"
    CREDIT_LIMIT_APPROVED = "evt.credit.limit.approved"
    CREDIT_LIMIT_REJECTED = "evt.credit.limit.rejected"
    CREDIT_APPLICATION_PROCESSED = "evt.credit.application.processed"
    CREDIT_SCORE_UPDATED = "evt.credit.score.updated"
    CREDIT_LIMIT_UTILIZED = "evt.credit.limit.utilized"
    
    # Auth Events
    AUTH_USER_CREATED = "evt.auth.user.created"
    AUTH_USER_VERIFIED = "evt.auth.user.verified"
    AUTH_PASSWORD_RESET = "evt.auth.password.reset"
    AUTH_LOGIN_SUCCESSFUL = "evt.auth.login.successful"
    AUTH_LOGIN_FAILED = "evt.auth.login.failed"
    AUTH_TOKENS_REVOKED = "evt.auth.tokens.revoked"
    
    # Profile Events
    PROFILE_CREATED = "evt.profile.created"
    PROFILE_UPDATED = "evt.profile.updated"
    PROFILE_SELFIE_VERIFIED = "evt.profile.selfie.verified"
    PROFILE_SELFIE_REJECTED = "evt.profile.selfie.rejected"
    PROFILE_BEHAVIOR_ANALYZED = "evt.profile.behavior.analyzed"
    PROFILE_RISK_SCORE_UPDATED = "evt.profile.risk_score.updated"
    
    # Notification Events
    NOTIFICATION_EMAIL_SENT = "evt.notification.email.sent"
    NOTIFICATION_DELIVERY_FAILED = "evt.notification.delivery.failed"
    
    # Analytics Events
    ANALYTICS_EVENT_TRACKED = "evt.analytics.event.tracked"
    ANALYTICS_REPORT_GENERATED = "evt.analytics.report.generated"
    ANALYTICS_EXPORT_COMPLETED = "evt.analytics.export.completed"
    ANALYTICS_ANOMALY_DETECTED = "evt.analytics.anomaly.detected"
    
    # Rate Limit Events
    RATE_LIMIT_EXCEEDED = "evt.rate_limit.exceeded"
    RATE_LIMIT_WARNING = "evt.rate_limit.warning"
    RATE_LIMIT_RESET = "evt.rate_limit.reset"
    
    # Webhook Events
    WEBHOOK_REGISTERED = "evt.webhook.registered"
    WEBHOOK_DELIVERED = "evt.webhook.delivered"
    WEBHOOK_DELIVERY_FAILED = "evt.webhook.delivery.failed"
    WEBHOOK_RETRY_SCHEDULED = "evt.webhook.retry.scheduled"
    
    # Scheduler Events
    SCHEDULER_JOB_CREATED = "evt.scheduler.job.created"
    SCHEDULER_JOB_EXECUTED = "evt.scheduler.job.executed"
    SCHEDULER_JOB_FAILED = "evt.scheduler.job.failed"
    SCHEDULER_JOB_CANCELLED = "evt.scheduler.job.cancelled"

