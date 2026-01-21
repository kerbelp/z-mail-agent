"""Email classification node for LangGraph workflow."""
import logging
from langgraph.graph import END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from models import AgentState, SubmissionCheck
from email_providers.base import EmailProvider
from config import CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)

# Initialize LLM
model = ChatOpenAI(model="gpt-4o", temperature=0)
structured_llm = model.with_structured_output(SubmissionCheck)


def create_classify_node(email_provider: EmailProvider):
    """
    Factory function to create a classify node with the given email provider.
    
    Args:
        email_provider: EmailProvider implementation to use
        
    Returns:
        Classify node function
    """
    def classify_email_node(state: AgentState):
        """Classify the current email without taking action."""
        idx = state["current_index"]
        
        if idx >= len(state["emails"]):
            return state
        
        email = state["emails"][idx]
        message_id = email.get("messageId")
        folder_id = email.get("folderId")
        subject = email.get("subject", "")
        from_address = email.get("fromAddress", "")
        
        logger.info(
            f"Classifying email {idx + 1}/{len(state['emails'])}: "
            f"{subject} (from {from_address})"
        )
        
        # Fetch full email content
        content = email_provider.get_email_content(message_id, folder_id)
        
        # Build prompt with full content
        prompt = f"Subject: {subject}\n\nContent:\n{content}"
        
        try:
            # Classify email
            response = structured_llm.invoke([
                SystemMessage(content=CLASSIFICATION_PROMPT),
                HumanMessage(content=prompt)
            ])
            
            return {
                "emails": state["emails"],
                "processed_count": state["processed_count"],
                "replied_count": state["replied_count"],
                "current_index": idx,
                "errors": state["errors"],
                "current_email": email,
                "classification_result": response
            }
        except Exception as e:
            logger.error(f"Error classifying email: {str(e)}")
            new_errors = state["errors"]
            new_errors.append(f"Error classifying email {idx}: {str(e)}")
            
            # Create default response for error case
            default_response = SubmissionCheck(
                is_article_submission=False,
                email_type="other"
            )
            
            return {
                "emails": state["emails"],
                "processed_count": state["processed_count"],
                "replied_count": state["replied_count"],
                "current_index": idx,
                "errors": new_errors,
                "current_email": email,
                "classification_result": default_response
            }
    
    return classify_email_node


def classification_router(state: AgentState):
    """Route based on email classification."""
    # If no emails to process, go to END
    if state["current_index"] >= len(state["emails"]):
        return END
    
    if not state.get("classification_result"):
        return "skip_email"
    
    email_type = state["classification_result"].email_type
    if email_type == "article_submission":
        return "handle_article_submission"
    else:
        return "skip_email"
