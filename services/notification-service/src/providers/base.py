from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class EmailMessage:
    """Email message structure"""
    to_email: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class EmailResult:
    """Email send result"""
    success: bool
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None

class EmailProvider(ABC):
    """Base email provider interface"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.from_email = config.get('from_email', 'noreply@glamyouup.com')
        self.from_name = config.get('from_name', 'GlamYouUp')
    
    @abstractmethod
    async def send_email(self, message: EmailMessage) -> EmailResult:
        """Send a single email"""
        pass
    
    @abstractmethod
    async def send_bulk_emails(self, messages: List[EmailMessage]) -> List[EmailResult]:
        """Send multiple emails"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        pass