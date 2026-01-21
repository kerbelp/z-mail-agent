"""Email ingestion node for LangGraph workflow."""
import logging
from models import AgentState
from email_providers.base import EmailProvider
from config import READ_EMAIL_LIMIT, PROCESSED_LABEL_ID

logger = logging.getLogger(__name__)


def create_ingest_node(email_provider: EmailProvider):
    """
    Factory function to create an ingest node with the given email provider.
    
    Args:
        email_provider: EmailProvider implementation to use
        
    Returns:
        Ingest node function
    """
    def ingest_emails_node(state: AgentState):
        """Fetches the latest unread emails into the state."""
        if not PROCESSED_LABEL_ID:
            logger.warning("PROCESSED_LABEL_ID is not configured - will process all emails without filtering")
        
        unread_emails = email_provider.fetch_unread_emails(
            limit=READ_EMAIL_LIMIT,
            exclude_label_id=PROCESSED_LABEL_ID
        )
        
        if len(unread_emails) == 0:
            logger.info("No unread emails to process")
        else:
            logger.info(f"Start processing {len(unread_emails)} email{'s' if len(unread_emails) > 1 else ''}")
        
        return {
            "emails": unread_emails,
            "processed_count": 0,
            "replied_count": 0,
            "current_index": 0,
            "errors": [],
            "current_email": {},
            "classification_result": None
        }
    
    return ingest_emails_node
