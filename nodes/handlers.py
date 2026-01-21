"""Email handler nodes for LangGraph workflow."""
import logging
from pathlib import Path
from langgraph.graph import END

from models import AgentState
from email_providers.base import EmailProvider
from config import RUN_CONFIG, PROCESSED_LABEL_ID

logger = logging.getLogger(__name__)


def load_template(template_path: str) -> str:
    """Load reply template from file."""
    full_path = Path(__file__).parent.parent / template_path
    with open(full_path, 'r') as f:
        return f.read().strip()


def create_classification_handler(email_provider: EmailProvider):
    """
    Factory function to create a generic classification handler.
    
    This single handler dispatches based on the classification result's action field.
    
    Args:
        email_provider: EmailProvider implementation to use
        
    Returns:
        Generic classification handler function
    """
    def handle_classification_node(state: AgentState):
        """Handle email based on classification result."""
        email = state["current_email"]
        classification = state["classification_result"]
        
        if not classification:
            logger.warning("No classification result - skipping email")
            return _skip_email(state, email, email_provider)
        
        message_id = email.get("messageId")
        folder_id = email.get("folderId")
        from_address = email.get("fromAddress", "")
        subject = email.get("subject", "")
        
        logger.info(
            f"[{classification.classification_name.upper()}] "
            f"Processing email from {from_address} with action: {classification.action}"
        )
        
        # Dispatch based on action
        if classification.action == "reply":
            return _handle_reply(state, email, classification, email_provider)
        elif classification.action == "skip":
            # Don't label emails that failed classification (classification_name == "error")
            should_label = classification.classification_name != "error"
            return _skip_email(state, email, email_provider, should_label=should_label)
        elif classification.action == "forward":
            # Future implementation
            logger.warning(f"Forward action not yet implemented")
            return _skip_email(state, email, email_provider)
        elif classification.action == "label":
            # Future implementation
            logger.warning(f"Label action not yet implemented")
            return _skip_email(state, email, email_provider)
        else:
            logger.error(f"Unknown action: {classification.action}")
            return _skip_email(state, email, email_provider)
    
    return handle_classification_node


def _handle_reply(state: AgentState, email: dict, classification, email_provider: EmailProvider):
    """Handle reply action."""
    message_id = email.get("messageId")
    folder_id = email.get("folderId")
    from_address = email.get("fromAddress", "")
    subject = email.get("subject", "")
    
    new_replied_count = state["replied_count"]
    new_errors = state["errors"]
    
    # Load reply template
    if not classification.reply_template:
        logger.error(f"No reply template configured for {classification.classification_name}")
        new_errors.append(f"No reply template for {classification.classification_name}")
        return _skip_email(state, email, email_provider)
    
    try:
        reply_content = load_template(classification.reply_template)
    except Exception as e:
        logger.error(f"Error loading template {classification.reply_template}: {str(e)}")
        new_errors.append(f"Error loading template: {str(e)}")
        return _skip_email(state, email, email_provider)
    
    if RUN_CONFIG.dry_run:
        logger.info(f"[DRY_RUN] Would send reply to {from_address}")
        if message_id and folder_id and PROCESSED_LABEL_ID:
            email_provider.apply_label(message_id, folder_id, PROCESSED_LABEL_ID)
        elif not PROCESSED_LABEL_ID:
            logger.warning("PROCESSED_LABEL_ID is not configured - skipping label application")
        new_replied_count += 1
    else:
        if RUN_CONFIG.send_reply:
            success = email_provider.send_reply(
                message_id,
                from_address,
                subject,
                reply_content
            )
            if success:
                logger.info(f"[REPLY_SENT] Successfully sent reply to {from_address}")
                new_replied_count += 1
                if message_id:
                    email_provider.mark_as_read(message_id)
            else:
                new_errors.append(f"Failed to reply to {from_address}")
        
        if RUN_CONFIG.add_label and message_id and folder_id and PROCESSED_LABEL_ID:
            email_provider.apply_label(message_id, folder_id, PROCESSED_LABEL_ID)
        elif not PROCESSED_LABEL_ID:
            logger.warning("PROCESSED_LABEL_ID is not configured - skipping label application")
    
    return {
        "emails": state["emails"],
        "processed_count": state["processed_count"] + 1,
        "replied_count": new_replied_count,
        "current_index": state["current_index"] + 1,
        "errors": new_errors,
        "current_email": {},
        "classification_result": None
    }


def _skip_email(state: AgentState, email: dict, email_provider: EmailProvider, should_label: bool = True):
    """Skip email and optionally mark as processed."""
    message_id = email.get("messageId")
    folder_id = email.get("folderId")
    logger.info(f"[SKIP] Skipping email {message_id}, subject: {email.get('subject')}")
    
    # Only label if should_label is True (don't label failed classifications)
    if should_label:
        if RUN_CONFIG.add_label and message_id and folder_id and PROCESSED_LABEL_ID:
            email_provider.apply_label(message_id, folder_id, PROCESSED_LABEL_ID)
        elif not PROCESSED_LABEL_ID:
            logger.warning("PROCESSED_LABEL_ID is not configured - skipping label application")
        else:
            logger.warning(f"Cannot apply label: message_id={message_id}, folder_id={folder_id}")
    else:
        logger.info(f"Not labeling email due to classification error - will retry on next run")
    
    return {
        "emails": state["emails"],
        "processed_count": state["processed_count"] + 1,
        "replied_count": state["replied_count"],
        "current_index": state["current_index"] + 1,
        "errors": state["errors"],
        "current_email": {},
        "classification_result": None
    }


def route_after_action(state: AgentState):
    """Route after handling: either loop or end."""
    if state["current_index"] < len(state["emails"]):
        return "classify"
    return END
