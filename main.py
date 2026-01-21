"""Email assistant powered by LangGraph and LLMs."""
import sys
import logging
from langgraph.graph import StateGraph, START, END

from config import RUN_CONFIG, setup_logging
from models import AgentState
from email_providers import ZohoEmailProvider
from nodes import (
    create_ingest_node,
    create_classify_node,
    classification_router,
    create_article_submission_handler,
    create_skip_handler,
    route_after_action
)

# Configure logging
logger = logging.getLogger(__name__)
setup_logging()


def build_workflow():
    """Build the LangGraph workflow with all nodes and edges."""
    # Initialize email provider
    email_provider = ZohoEmailProvider()
    
    # Create node functions with dependency injection
    ingest_node = create_ingest_node(email_provider)
    classify_node = create_classify_node(email_provider)
    article_handler = create_article_submission_handler(email_provider)
    skip_handler = create_skip_handler(email_provider)
    
    # Build workflow graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("ingest", ingest_node)
    workflow.add_node("classify", classify_node)
    workflow.add_node("handle_article_submission", article_handler)
    workflow.add_node("skip_email", skip_handler)
    
    # Add edges
    workflow.add_edge(START, "ingest")
    workflow.add_edge("ingest", "classify")
    
    # Conditional routing from classify node
    workflow.add_conditional_edges("classify", classification_router, {
        "handle_article_submission": "handle_article_submission",
        "skip_email": "skip_email",
        END: END
    })
    
    # Conditional routing after action nodes (loop or end)
    workflow.add_conditional_edges("handle_article_submission", route_after_action, {
        "classify": "classify",
        END: END
    })
    workflow.add_conditional_edges("skip_email", route_after_action, {
        "classify": "classify",
        END: END
    })
    
    return workflow.compile()


def main():
    """Main execution function."""
    logger.info("Starting email assistant workflow")
    logger.info(f"Configuration: debug={RUN_CONFIG.debug}, dry_run={RUN_CONFIG.dry_run}, "
                f"send_reply={RUN_CONFIG.send_reply}, add_label={RUN_CONFIG.add_label}")
    
    # Build workflow
    app = build_workflow()
    
    try:
        # Execute workflow
        final_state = app.invoke({
            "emails": [],
            "processed_count": 0,
            "replied_count": 0,
            "current_index": 0,
            "errors": [],
            "current_email": {},
            "classification_result": None
        })
        
        # Print summary
        is_terminal = sys.stdout.isatty()
        
        if is_terminal:
            # Formatted output for terminal
            logger.info("=" * 60)
            logger.info("WORKFLOW SUMMARY")
            logger.info("=" * 60)
            logger.info(f"✓ Total emails processed: {final_state['processed_count']}")
            logger.info(f"✓ Article submissions replied: {final_state['replied_count']}")
            
            if final_state['errors']:
                logger.warning(f"⚠ Errors encountered: {len(final_state['errors'])}")
                for error in final_state['errors']:
                    logger.warning(f"  - {error}")
            
            logger.info("=" * 60)
        else:
            # Compact output for logs/pipes
            error_msg = f", errors={len(final_state['errors'])}" if final_state['errors'] else ""
            logger.info(f"Workflow complete: processed={final_state['processed_count']}, "
                       f"replied={final_state['replied_count']}{error_msg}")
            if final_state['errors']:
                for error in final_state['errors']:
                    logger.warning(f"Error: {error}")
        
    except Exception as e:
        logger.error(f"Workflow failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
