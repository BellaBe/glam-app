from typing import List, Dict, Any, Optional
from shared.utils.logger import ServiceLogger
from shared.errors.utils import wrap_external_error
from shared.api.correlation import add_correlation_header

from ..providers.base import EmailProvider, EmailMessage, EmailResult
from ..providers.sendgrid import SendGridProvider
from ..providers.ses import SESProvider
from ..providers.smtp import SMTPProvider
from ..exceptions import EmailProviderError


class EmailService:
    """Email service with fallback support"""
    
    def __init__(self, config: dict, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        self.providers: Dict[str, EmailProvider] = {}
        self.current_provider = config.get('primary_provider')
        self._init_providers()
    
    def _init_providers(self):
        """Initialize email providers"""
        try:
            # SendGrid
            if self.config.get('sendgrid_config'):
                self.providers['sendgrid'] = SendGridProvider(self.config['sendgrid_config'])
            
            # SES
            if self.config.get('ses_config'):
                self.providers['ses'] = SESProvider(self.config['ses_config'])
            
            # SMTP
            if self.config.get('smtp_config'):
                self.providers['smtp'] = SMTPProvider(self.config['smtp_config'])
        except Exception as e:
            raise wrap_external_error(
                EmailProviderError,
                "Failed to initialize email providers",
                cause=e,
                provider="initialization"
            )
    
    async def send_email(self, message: EmailMessage) -> EmailResult:
        """Send email with automatic fallback"""
        if not isinstance(self.current_provider, str):
            raise EmailProviderError(
                "Current provider is not a valid string",
                provider=self.current_provider,
                provider_error_code="INVALID_PROVIDER"
            )
        primary_provider = self.providers.get(self.current_provider)
        
        if not primary_provider:
            raise EmailProviderError(
                f"Primary provider {self.current_provider} not configured",
                provider=self.current_provider,
                provider_error_code="NOT_CONFIGURED"
            )
        
        # Try primary provider
        try:
            self.logger.info(f"Sending email via primary provider: {self.current_provider}")
            add_correlation_header({})
            
            result = await primary_provider.send_email(message)
            
            if result.success:
                return result
            else:
                self.logger.warning(
                    f"Primary provider {self.current_provider} failed with error: {result.error_message}",
                    extra={"provider": self.current_provider}
                )
                result = EmailResult(
                    success=False,
                    provider=self.current_provider,
                    provider_message_id=result.provider_message_id,
                    error_message=result.error_message,
                    error_code=result.error_code or "PROVIDER_ERROR"
                )
                
                return result
        except Exception as e:
            self.logger.warning(
                f"Primary provider {self.current_provider} failed: {e}",
                extra={"provider": self.current_provider}
            )
            result = EmailResult(
                success=False,
                provider=self.current_provider,
                provider_message_id=None,
                error_message=str(e),
                error_code="PROVIDER_ERROR"
            )
    
        
        # Try fallback provider if primary fails
        fallback_name = self.config.get('fallback_provider')
        if fallback_name and fallback_name != self.current_provider:
            fallback_provider = self.providers.get(fallback_name)
            
            if fallback_provider:
                self.logger.info(f"Trying fallback provider {fallback_name}")
                self.current_provider = fallback_name
                
                try:
                    result = await fallback_provider.send_email(message)
                    
                    if result.success:
                        return result
                except Exception as e:
                    self.logger.error(
                        f"Fallback provider {fallback_name} also failed: {e}",
                        extra={"provider": fallback_name}
                    )
                    result = EmailResult(
                        success=False,
                        provider=fallback_name,
                        error_message=str(e),
                        error_code="PROVIDER_ERROR"
                    )
        
        # All providers failed
        raise EmailProviderError(
            "All email providers failed",
            provider=self.current_provider,
            provider_message=result.error_message,
            provider_error_code=result.error_code
        )
    
    async def send_bulk_emails(self, messages: List[EmailMessage]) -> List[EmailResult]:
        """Send bulk emails"""
        provider = self.providers.get(self.current_provider)
        
        if not provider:
            raise EmailProviderError(
                f"Provider {self.current_provider} not configured",
                provider=self.current_provider,
                provider_error_code="NOT_CONFIGURED"
            )
        
        try:
            return await provider.send_bulk_emails(messages)
        except Exception as e:
            raise wrap_external_error(
                EmailProviderError,
                f"Bulk send failed via {self.current_provider}",
                cause=e,
                provider=self.current_provider
            )
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all providers"""
        health_status = {}
        
        for name, provider in self.providers.items():
            try:
                health_status[name] = await provider.health_check()
            except Exception as e:
                self.logger.error(f"Health check failed for {name}: {e}")
                health_status[name] = False
        
        return health_status