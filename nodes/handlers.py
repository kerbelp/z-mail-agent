"""Email handler nodes for LangGraph workflow."""
import logging
from langgraph.graph import END

from models import AgentState
from email_providers.base import EmailProvider
from config import RUN_CONFIG, REPLY_TEMPLATE, PROCESSED_LABEL_ID

logger = logging.getLogger(__name__)


def create_article_submission_handler(email_provider: EmailProvider):
    """
    Factory function to create an article submission handler with the given email provider.
    
    Args:
        email_provider: EmailProvider implementation to use
        
    Returns:
        Article submission handler function
    """
    def handle_article_submission_node(state: AgentState):
        """Handle article submission email."""
        email = state["current_email"]
        message_id = email.get("messageId")
        folder_id = email.get("folderId")
        from_address = email.get("fromAddress", "")
        subject = email.get("subject", "")
        
        logger.info(f"[ARTICLE_SUBMISSION] Handling article submission from {from_address}")
        
        new_replied_count = state["replied_count"]
        new_errors = state["errors"]
        
        if RUN_CONFIG.dry_run:
            logger.info(f"[DRY_RUN] Would handle article submission from {from_address}")
            if message_id and folder_id and PROCESSED_LABEL_ID:
                email_provider.apply_label(message_id, folder_id, PROCESSED_LABEL_ID)
            elif not PROCESSED_LABEL_ID:
                logger.warning("PROCESSED_LABEL_ID is not configured - skipping label application")
            new_replied_count += 1
        else:
            success = email_provider.send_reply(
                message_id,
                from_address,
                subject,
                REPLY_TEMPLATE
            )
            if success:
                logger.info(f"[REPLY_SENT] Successfully sent reply to {from_address}")
                new_replied_count += 1
                if message_id:
                    email_provider.mark_as_read(message_id)
                if message_id and folder_id and PROCESSED_LABEL_ID:
                    email_provider.apply_label(message_id, folder_id, PROCESSED_LABEL_ID)
                elif not PROCESSED_LABEL_ID:
                    logger.warning("PROCESSED_LABEL_ID is not configured - skipping label application")
            else:
                new_errors.append(f"Failed to reply to {from_address}")
        
        return {
            "emails": state["emails"],
            "processed_count": state["processed_count"] + 1,
            "replied_count": new_replied_count,
            "current_index": state["current_index"] + 1,
            "errors": new_errors,
            "current_email": {},
            "classification_result": None
        }
    
    return handle_article_submission_node


def create_skip_handler(email_provider: EmailProvider):
    """
    Factory function to create a skip handler with the given email provider.
    
    Args:
        email_provider: EmailProvider implementation to use
        
    Returns:
        Skip handler function
    """
    def skip_email_node(state: AgentState):
        """Skip emails that don't match any category."""
        email = state["current_email"]
        message_id = email.get("messageId")
        folder_id = email.get("folderId")
        logger.info(f"[SKIP] Skipping email {message_id}, subject: {email.get('subject')}")
        
        # Also label skipped emails so we don't re-process them
        if message_id and folder_id and PROCESSED_LABEL_ID:
            email_provider.apply_label(message_id, folder_id, PROCESSED_LABEL_ID)
        elif not PROCESSED_LABEL_ID:
            logger.warning("PROCESSED_LABEL_ID is not configured - skipping label application")
        else:
            logger.warning(f"Cannot apply label: message_id={message_id}, folder_id={folder_id}")
        
        return {
            "emails": state["emails"],
            "processed_count": state["processed_count"] + 1,
            "replied_count": state["replied_count"],
            "current_index": state["current_index"] + 1,
            "errors": state["errors"],
            "current_email": {},
            "classification_result": None
        }
    
    return skip_email_node


def route_after_action(state: AgentState):
    """Route after handling or skipping: either loop or end."""
    if state["current_index"] < len(state["emails"]):
        return "classify"
    return END
