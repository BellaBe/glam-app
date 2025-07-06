import httpx
from typing import List, Dict, Any
from shared.errors.utils import classify_http_error
from shared.api.correlation import add_correlation_header
from .base import EmailProvider, EmailMessage, EmailResult
from src.models import NotificationProvider
import asyncio

class SendGridProvider(EmailProvider):
    """SendGrid email provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.base_url = "https://api.sendgrid.com/v3"
        self.timeout = config.get('timeout_seconds', 30)
    
    async def send_email(self, message: EmailMessage) -> EmailResult:
        """Send email via SendGrid"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Add correlation header for tracing
            headers = add_correlation_header(headers)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/mail/send",
                    headers=headers,
                    json={
                        "personalizations": [{
                            "to": [{"email": message.to_email}]
                        }],
                        "from": {
                            "email": self.from_email,
                            "name": self.from_name
                        },
                        "subject": message.subject,
                        "content": [
                            {"type": "text/html", "value": message.html_body},
                            {"type": "text/plain", "value": message.text_body or ""}
                        ]
                    },
                    timeout=self.timeout
                )
                
                if response.status_code in (200, 202):
                    return EmailResult(
                        success=True,
                        provider=NotificationProvider.SENDGRID,
                        provider_message_id=response.headers.get('X-Message-Id')
                    )
                else:
                    # Parse SendGrid error response
                    error_data = response.json()
                    errors = error_data.get('errors', [])
                    error_message = errors[0].get('message') if errors else response.text
                    
                    return EmailResult(
                        success=False,
                        provider=NotificationProvider.SENDGRID,
                        error_message=error_message,
                        error_code=f"SENDGRID_{response.status_code}"
                    )
                    
        except httpx.HTTPError as e:
            # Use shared error classification
            infra_error = classify_http_error(e, service_name="SendGrid")
            
            return EmailResult(
                success=False,
                provider=NotificationProvider.SENDGRID,
                error_message=str(infra_error),
                error_code=infra_error.code
            )
        except Exception as e:
            return EmailResult(
                success=False,
                provider=NotificationProvider.SENDGRID,
                error_message=str(e),
                error_code="NETWORK_ERROR"
            )
    
    async def send_bulk_emails(self, messages: List[EmailMessage]) -> List[EmailResult]:
        """Send bulk emails via SendGrid"""
        # SendGrid supports batch sending, but we'll use concurrent single sends
        # for simplicity and better error handling per email
        tasks = [self.send_email(message) for message in messages]
        return await asyncio.gather(*tasks)
    
    async def health_check(self) -> bool:
        """Check SendGrid API health"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            headers = add_correlation_header(headers)
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/scopes",
                    headers=headers,
                    timeout=5
                )
                return response.status_code == 200
        except:
            return False