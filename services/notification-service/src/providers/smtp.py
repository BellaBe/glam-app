import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from .base import EmailProvider, EmailMessage, EmailResult
from src.models import NotificationProvider
from shared.api.correlation import get_correlation_context
import asyncio
import uuid

class SMTPProvider(EmailProvider):
    """SMTP email provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 1025)
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.use_tls = config.get('use_tls', False)  # MailHog doesn't need TLS
        self.timeout = config.get('timeout', 30)
    
    async def send_email(self, message: EmailMessage) -> EmailResult:
        """Send email via SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = message.subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = message.to_email
            
            # Add correlation ID as a custom header
            correlation_id = get_correlation_context()
            if correlation_id:
                msg['X-Correlation-ID'] = correlation_id
            
            # Generate message ID if not already set
            if 'Message-ID' not in msg:
                msg['Message-ID'] = f"<{uuid.uuid4()}@{self.from_email.split('@')[1]}>"
            
            # Add text and HTML parts
            if message.text_body:
                text_part = MIMEText(message.text_body, 'plain', 'utf-8')
                msg.attach(text_part)
            
            html_part = MIMEText(message.html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Send email
            async with aiosmtplib.SMTP(
                hostname=self.host,
                port=self.port,
                timeout=self.timeout,
                use_tls=self.use_tls
            ) as smtp:
                if self.username and self.password:
                    await smtp.login(self.username, self.password)
                
                response = await smtp.send_message(msg)
                
                # Check if email was sent successfully
                failed_recipients = response[0].get(message.to_email)
                if failed_recipients:
                    return EmailResult(
                        success=False,
                        provider=NotificationProvider.SMTP,
                        error_message=f"Failed to send to {message.to_email}",
                        error_code="SMTP_SEND_FAILED"
                    )
                
                return EmailResult(
                    success=True,
                    provider=NotificationProvider.SMTP,
                    provider_message_id=msg['Message-ID']
                )
                
        except aiosmtplib.SMTPAuthenticationError as e:
            return EmailResult(
                success=False,
                provider=NotificationProvider.SMTP,
                error_message=str(e),
                error_code="AUTHENTICATION_ERROR"
            )
        except aiosmtplib.SMTPTimeoutError as e:
            return EmailResult(
                success=False,
                provider=NotificationProvider.SMTP,
                error_message=str(e),
                error_code="PROVIDER_TIMEOUT"
            )
        except aiosmtplib.SMTPResponseException as e:
            # Handle specific SMTP errors
            if e.code == 550:  # Recipient rejected
                return EmailResult(
                    success=False,
                    provider=NotificationProvider.SMTP,
                    error_message=str(e),
                    error_code="INVALID_RECIPIENT"
                )
            else:
                return EmailResult(
                    success=False,
                    provider=NotificationProvider.SMTP,
                    error_message=str(e),
                    error_code="SMTP_ERROR"
                )
        except Exception as e:
            return EmailResult(
                success=False,
                provider=NotificationProvider.SMTP,
                error_message=str(e),
                error_code="NETWORK_ERROR"
            )
    
    async def send_bulk_emails(self, messages: List[EmailMessage]) -> List[EmailResult]:
        """Send bulk emails via SMTP"""
        # For SMTP, we'll send emails sequentially to avoid overwhelming the server
        results = []
        
        try:
            async with aiosmtplib.SMTP(
                hostname=self.host,
                port=self.port,
                timeout=self.timeout,
                use_tls=self.use_tls
            ) as smtp:
                if self.username and self.password:
                    await smtp.login(self.username, self.password)
                
                for message in messages:
                    # Create message
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = message.subject
                    msg['From'] = f"{self.from_name} <{self.from_email}>"
                    msg['To'] = message.to_email
                    
                    # Add correlation ID
                    correlation_id = get_correlation_context()
                    if correlation_id:
                        msg['X-Correlation-ID'] = correlation_id
                    
                    # Generate message ID
                    if 'Message-ID' not in msg:
                        msg['Message-ID'] = f"<{uuid.uuid4()}@{self.from_email.split('@')[1]}>"
                    
                    # Add parts
                    if message.text_body:
                        text_part = MIMEText(message.text_body, 'plain', 'utf-8')
                        msg.attach(text_part)
                    
                    html_part = MIMEText(message.html_body, 'html', 'utf-8')
                    msg.attach(html_part)
                    
                    # Send
                    try:
                        response = await smtp.send_message(msg)
                        failed = response[0].get(message.to_email)
                        
                        if failed:
                            results.append(EmailResult(
                                success=False,
                                provider=NotificationProvider.SMTP,
                                error_message=f"Failed to send to {message.to_email}",
                                error_code="SMTP_SEND_FAILED"
                            ))
                        else:
                            results.append(EmailResult(
                                success=True,
                                provider=NotificationProvider.SMTP,
                                provider_message_id=msg['Message-ID']
                            ))
                    except Exception as e:
                        results.append(EmailResult(
                            success=False,
                            provider=NotificationProvider.SMTP,
                            error_message=str(e),
                            error_code="SMTP_ERROR"
                        ))
        except Exception as e:
            # Connection failed, all emails fail
            return [
                EmailResult(
                    success=False,
                    provider=NotificationProvider.SMTP,
                    error_message=str(e),
                    error_code="NETWORK_ERROR"
                ) for _ in messages
            ]
        
        return results
    
    async def health_check(self) -> bool:
        """Check SMTP server availability"""
        try:
            # For MailHog or other dev SMTP servers without auth
            if not self.username and not self.password:
                # Just try to connect without auth
                import smtplib
                with smtplib.SMTP(self.host, self.port, timeout=5) as server:
                    # MailHog doesn't need STARTTLS or auth
                    return True
            else:
                # Production SMTP with auth
                import smtplib
                with smtplib.SMTP(self.host, self.port, timeout=5) as server:
                    if self.use_tls and self.port != 25:
                        server.starttls()
                    if self.username and self.password:
                        server.login(self.username, self.password)
                    return True
        except Exception as e:
            print(f"SMTP health check failed: {e}")
            return False