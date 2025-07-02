import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from .base import EmailProvider, EmailMessage, EmailResult
import asyncio

class SMTPProvider(EmailProvider):
    """SMTP email provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 587)
        self.username = config.get('username')
        self.password = config.get('password')
        self.use_tls = config.get('use_tls', True)
        self.timeout = config.get('timeout_seconds', 30)
    
    async def send_email(self, message: EmailMessage) -> EmailResult:
        """Send email via SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = message.subject
            msg['From'] = f"{message.from_name or self.from_name} <{message.from_email or self.from_email}>"
            msg['To'] = message.to_email
            
            # Add text and HTML parts
            if message.text_content:
                text_part = MIMEText(message.text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            html_part = MIMEText(message.html_content, 'html', 'utf-8')
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
                failed_recipients = response.get(message.to_email)
                if failed_recipients:
                    return EmailResult(
                        success=False,
                        error_message=f"Failed to send to {message.to_email}",
                        error_code="SMTP_SEND_FAILED"
                    )
                
                return EmailResult(
                    success=True,
                    provider_message_id=msg['Message-ID']
                )
                
        except aiosmtplib.SMTPAuthenticationError as e:
            return EmailResult(
                success=False,
                error_message=str(e),
                error_code="AUTHENTICATION_ERROR"
            )
        except aiosmtplib.SMTPTimeoutError as e:
            return EmailResult(
                success=False,
                error_message=str(e),
                error_code="PROVIDER_TIMEOUT"
            )
        except aiosmtplib.SMTPResponseException as e:
            # Handle specific SMTP errors
            if e.code == 550:  # Recipient rejected
                return EmailResult(
                    success=False,
                    error_message=str(e),
                    error_code="INVALID_RECIPIENT"
                )
            else:
                return EmailResult(
                    success=False,
                    error_message=str(e),
                    error_code="SMTP_ERROR"
                )
        except Exception as e:
            return EmailResult(
                success=False,
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
                    msg['From'] = f"{message.from_name or self.from_name} <{message.from_email or self.from_email}>"
                    msg['To'] = message.to_email
                    
                    # Add parts
                    if message.text_content:
                        text_part = MIMEText(message.text_content, 'plain', 'utf-8')
                        msg.attach(text_part)
                    
                    html_part = MIMEText(message.html_content, 'html', 'utf-8')
                    msg.attach(html_part)
                    
                    # Send
                    try:
                        response = await smtp.send_message(msg)
                        failed = response.get(message.to_email)
                        
                        if failed:
                            results.append(EmailResult(
                                success=False,
                                error_message=f"Failed to send to {message.to_email}",
                                error_code="SMTP_SEND_FAILED"
                            ))
                        else:
                            results.append(EmailResult(
                                success=True,
                                provider_message_id=msg['Message-ID']
                            ))
                    except Exception as e:
                        results.append(EmailResult(
                            success=False,
                            error_message=str(e),
                            error_code="SMTP_ERROR"
                        ))
        except Exception as e:
            # Connection failed, all emails fail
            return [
                EmailResult(
                    success=False,
                    error_message=str(e),
                    error_code="NETWORK_ERROR"
                ) for _ in messages
            ]
        
        return results
    
    async def health_check(self) -> bool:
        """Check SMTP server health"""
        try:
            async with aiosmtplib.SMTP(
                hostname=self.host,
                port=self.port,
                timeout=5,
                use_tls=self.use_tls
            ) as smtp:
                if self.username and self.password:
                    await smtp.login(self.username, self.password)
                
                # Just check we can connect
                await smtp.noop()
                return True
        except:
            return False