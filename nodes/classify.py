"""Email classification node for LangGraph workflow."""
import logging
import yaml
from pathlib import Path
from langgraph.graph import END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from models import AgentState, ClassificationResult, EmailClassification
from email_providers.base import EmailProvider

logger = logging.getLogger(__name__)

# Initialize LLM
model = ChatOpenAI(model="gpt-4o", temperature=0)
structured_llm = model.with_structured_output(ClassificationResult)


def load_classifications():
    """Load classifications from YAML config file."""
    config_path = Path(__file__).parent.parent / "classifications.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Sort by priority
    classifications = sorted(config['classifications'], key=lambda x: x['priority'])
    return classifications


def load_prompt(prompt_path: str) -> str:
    """Load classification prompt from file."""
    full_path = Path(__file__).parent.parent / prompt_path
    with open(full_path, 'r') as f:
        return f.read().strip()


def create_classify_node(email_provider: EmailProvider):
    """
    Factory function to create a classify node with the given email provider.
    
    Args:
        email_provider: EmailProvider implementation to use
        
    Returns:
        Classify node function
    """
    def classify_email_node(state: AgentState):
        """Classify the current email using waterfall approach."""
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
        email_prompt = f"Subject: {subject}\n\nContent:\n{content}"
        
        try:
            # Load classifications config
            classifications = load_classifications()
            
            # Try each classification in priority order (waterfall)
            for classification_config in classifications:
                classification_name = classification_config['name']
                prompt_file = classification_config['classification_prompt']
                
                logger.debug(f"Testing classification: {classification_name}")
                
                # Load the specific classification prompt
                system_prompt = load_prompt(prompt_file)
                
                # Classify email
                response = structured_llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=email_prompt)
                ])
                
                # If this classification matches, use it
                if response.match:
                    logger.info(
                        f"[CLASSIFIED] {classification_name} "
                        f"(confidence: {response.confidence:.2f}) - {response.reasoning}"
                    )
                    
                    email_classification = EmailClassification(
                        classification_name=classification_name,
                        confidence=response.confidence,
                        reasoning=response.reasoning,
                        action=classification_config['action'],
                        reply_template=classification_config.get('reply_template')
                    )
                    
                    return {
                        "emails": state["emails"],
                        "processed_count": state["processed_count"],
                        "replied_count": state["replied_count"],
                        "current_index": idx,
                        "errors": state["errors"],
                        "current_email": email,
                        "classification_result": email_classification
                    }
            
            # No classification matched - default to skip
            logger.info("[UNCLASSIFIED] No classification matched, will skip")
            
            email_classification = EmailClassification(
                classification_name="unclassified",
                confidence=1.0,
                reasoning="No classification matched",
                action="skip",
                reply_template=None
            )
            
            return {
                "emails": state["emails"],
                "processed_count": state["processed_count"],
                "replied_count": state["replied_count"],
                "current_index": idx,
                "errors": state["errors"],
                "current_email": email,
                "classification_result": email_classification
            }
            
        except Exception as e:
            error_msg = str(e)
            
            # Check if this is a rate limit error
            is_rate_limit = "rate_limit" in error_msg.lower() or "429" in error_msg
            
            if is_rate_limit:
                logger.warning(f"Rate limit encountered on email {idx}, will retry automatically")
            else:
                logger.error(f"Error classifying email: {error_msg}")
            
            # Only add to errors list if it's not a rate limit (those are retried automatically)
            # If rate limit retry fails, it will raise again and get caught here as a different error
            if not is_rate_limit:
                new_errors = state["errors"]
                new_errors.append(f"Error classifying email {idx}: {error_msg}")
            else:
                new_errors = state["errors"]
            
            return {
                "emails": state["emails"],
                "processed_count": state["processed_count"],
                "replied_count": state["replied_count"],
                "current_index": idx,
                "errors": new_errors,
                "current_email": email,
                "classification_result": None
            }
    
    return classify_email_node


def classification_router(state: AgentState):
    """Route based on email classification - now just routes to single handler."""
    # If no emails to process, go to END
    if state["current_index"] >= len(state["emails"]):
        return END
    
    if not state.get("classification_result"):
        return END
    
    # All classifications go to the same generic handler
    return "handle_classification"
