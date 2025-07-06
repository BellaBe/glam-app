import boto3
from botocore.exceptions import ClientError
from typing import List, Dict, Any
from .base import EmailProvider, EmailMessage, EmailResult
from src.models import NotificationProvider
from shared.api.correlation import get_correlation_context
import asyncio

class SESProvider(EmailProvider):
    """AWS SES email provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.region = config.get('region', 'us-east-1')
        
        # Get correlation ID for AWS request context
        correlation_id = get_correlation_context()
        
        # Create client with custom config including correlation ID in user agent
        client_config = {
            'region_name': self.region
        }
        
        if config.get('aws_access_key_id'):
            client_config['aws_access_key_id'] = config.get('aws_access_key_id')
        if config.get('aws_secret_access_key'):
            client_config['aws_secret_access_key'] = config.get('aws_secret_access_key')
            
        self.client = boto3.client('ses', **client_config)
        
        # If we have correlation ID, add it to the client metadata
        if correlation_id:
            self.client._client_config.user_agent_extra = f'correlation_id/{correlation_id}'
    
    async def send_email(self, message: EmailMessage) -> EmailResult:
        """Send email via AWS SES"""
        try:
            # Run boto3 call in thread pool since it's sync
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._send_email_sync,
                message
            )
            
            return EmailResult(
                success=True,
                provider=NotificationProvider.AWS_SES,
                provider_message_id=response['MessageId']
            )
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            # Map AWS errors to our error codes
            if error_code == 'MessageRejected':
                return EmailResult(
                    success=False,
                    provider=NotificationProvider.AWS_SES,
                    error_message=error_message,
                    error_code="INVALID_RECIPIENT"
                )
            elif error_code == 'Throttling':
                return EmailResult(
                    success=False,
                    provider=NotificationProvider.AWS_SES,
                    error_message=error_message,
                    error_code="PROVIDER_RATE_LIMITED"
                )
            elif error_code == 'MailFromDomainNotVerified':
                return EmailResult(
                    success=False,
                    provider=NotificationProvider.AWS_SES,
                    error_message=error_message,
                    error_code="CONFIGURATION_ERROR"
                )
            else:
                return EmailResult(
                    success=False,
                    provider=NotificationProvider.AWS_SES,
                    error_message=error_message,
                    error_code="PROVIDER_ERROR"
                )
                
        except Exception as e:
            return EmailResult(
                success=False,
                provider=NotificationProvider.AWS_SES,
                error_message=str(e),
                error_code="NETWORK_ERROR"
            )
    
    def _send_email_sync(self, message: EmailMessage) -> dict:
        """Synchronous email send for thread pool"""
        # Add correlation ID as a message tag if available
        correlation_id = get_correlation_context()
        
        email_params = {
            'Source': f"{self.from_name} <{self.from_email}>",
            'Destination': {
                'ToAddresses': [message.to_email]
            },
            'Message': {
                'Subject': {
                    'Data': message.subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Html': {
                        'Data': message.html_body,
                        'Charset': 'UTF-8'
                    },
                    'Text': {
                        'Data': message.text_body or '',
                        'Charset': 'UTF-8'
                    }
                }
            }
        }
        
        # Add correlation ID as a tag if available
        if correlation_id:
            email_params['Tags'] = [
                {
                    'Name': 'correlation_id',
                    'Value': correlation_id
                }
            ]
        
        return self.client.send_email(**email_params)
    
    async def send_bulk_emails(self, messages: List[EmailMessage]) -> List[EmailResult]:
        """Send bulk emails via SES"""
        # SES supports bulk sending, but for simplicity we'll use concurrent single sends
        tasks = [self.send_email(message) for message in messages]
        return await asyncio.gather(*tasks)
    
    async def health_check(self) -> bool:
        """Check SES health"""
        try:
            loop = asyncio.get_event_loop()
            # Try to get send quota
            await loop.run_in_executor(
                None,
                self.client.get_send_quota
            )
            return True
        except:
            return False