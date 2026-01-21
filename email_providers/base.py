"""Abstract base class for email provider implementations."""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class EmailProvider(ABC):
    """
    Abstract base class for email provider implementations.
    
    This class defines the interface that all email providers must implement.
    Implementations can be created for different email services (Zoho, Gmail, Outlook, etc.).
    """
    
    @abstractmethod
    def fetch_unread_emails(self, limit: int, exclude_label_id: Optional[str] = None) -> List[Dict]:
        """
        Fetch unread emails from the email provider.
        
        Args:
            limit: Maximum number of emails to fetch
            exclude_label_id: Optional label ID to exclude from results
            
        Returns:
            List of email dictionaries with at least these keys:
            - messageId: Unique message identifier
            - folderId: Folder identifier
            - fromAddress: Sender email address
            - subject: Email subject
            - labelId: List of label IDs (if applicable)
        """
        pass
    
    @abstractmethod
    def get_email_content(self, message_id: str, folder_id: str) -> str:
        """
        Fetch full email content/body.
        
        Args:
            message_id: Unique message identifier
            folder_id: Folder identifier
            
        Returns:
            Email content as string (HTML or plain text)
        """
        pass
    
    @abstractmethod
    def send_reply(self, message_id: str, to_address: str, subject: str, content: str) -> bool:
        """
        Send a reply email.
        
        Args:
            message_id: Original message ID to reply to
            to_address: Recipient email address
            subject: Reply subject line
            content: Reply email body
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark an email as read.
        
        Args:
            message_id: Unique message identifier
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def apply_label(self, message_id: str, folder_id: str, label_id: str) -> bool:
        """
        Apply a label/tag to an email.
        
        Args:
            message_id: Unique message identifier
            folder_id: Folder identifier
            label_id: Label/tag identifier to apply
            
        Returns:
            True if successful, False otherwise
        """
        pass
