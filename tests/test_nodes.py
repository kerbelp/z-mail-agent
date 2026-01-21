"""Tests for workflow nodes."""
import pytest
from unittest.mock import Mock, patch

from nodes.ingest import create_ingest_node
from nodes.classify import create_classify_node, classification_router
from nodes.handlers import (
    create_article_submission_handler,
    create_skip_handler,
    route_after_action
)
from models import SubmissionCheck


class TestIngestNode:
    """Tests for email ingestion node."""
    
    def test_ingest_with_emails(self, mock_email_provider, sample_emails, initial_state):
        """Test ingestion when emails are found."""
        mock_email_provider.fetch_unread_emails.return_value = sample_emails
        
        ingest_node = create_ingest_node(mock_email_provider)
        result = ingest_node(initial_state)
        
        assert result["emails"] == sample_emails
        assert result["processed_count"] == 0
        assert result["replied_count"] == 0
        assert result["current_index"] == 0
        assert result["errors"] == []
    
    def test_ingest_with_no_emails(self, mock_email_provider, initial_state):
        """Test ingestion when no emails are found."""
        mock_email_provider.fetch_unread_emails.return_value = []
        
        ingest_node = create_ingest_node(mock_email_provider)
        result = ingest_node(initial_state)
        
        assert result["emails"] == []
        assert result["current_index"] == 0
    
    def test_ingest_with_missing_label_id(self, mock_email_provider, initial_state, monkeypatch):
        """Test ingestion when PROCESSED_LABEL_ID is not configured."""
        monkeypatch.setattr('nodes.ingest.PROCESSED_LABEL_ID', None)
        mock_email_provider.fetch_unread_emails.return_value = []
        
        ingest_node = create_ingest_node(mock_email_provider)
        result = ingest_node(initial_state)
        
        # Should complete successfully despite missing label ID
        assert "emails" in result


class TestClassifyNode:
    """Tests for email classification node."""
    
    def test_classify_email(self, mock_email_provider, sample_email):
        """Test email classification."""
        state = {
            "emails": [sample_email],
            "current_index": 0,
            "processed_count": 0,
            "replied_count": 0,
            "errors": [],
            "current_email": {},
            "classification_result": None
        }
        
        mock_email_provider.get_email_content.return_value = "I would like to submit an article"
        
        with patch('nodes.classify.structured_llm') as mock_llm:
            mock_llm.invoke.return_value = SubmissionCheck(
                is_article_submission=True,
                email_type="article_submission"
            )
            
            classify_node = create_classify_node(mock_email_provider)
            result = classify_node(state)
            
            assert result["current_email"] == sample_email
            assert result["classification_result"].email_type == "article_submission"
    
    def test_classify_out_of_range(self, mock_email_provider):
        """Test classification when index is out of range."""
        state = {
            "emails": [],
            "current_index": 0,
            "processed_count": 0,
            "replied_count": 0,
            "errors": [],
            "current_email": {},
            "classification_result": None
        }
        
        classify_node = create_classify_node(mock_email_provider)
        result = classify_node(state)
        
        # Should return state unchanged
        assert result == state


class TestClassificationRouter:
    """Tests for classification routing logic."""
    
    def test_router_to_article_submission(self):
        """Test routing to article submission handler."""
        state = {
            "emails": [{}],
            "current_index": 0,
            "classification_result": SubmissionCheck(
                is_article_submission=True,
                email_type="article_submission"
            )
        }
        
        route = classification_router(state)
        assert route == "handle_article_submission"
    
    def test_router_to_skip(self):
        """Test routing to skip handler."""
        state = {
            "emails": [{}],
            "current_index": 0,
            "classification_result": SubmissionCheck(
                is_article_submission=False,
                email_type="other"
            )
        }
        
        route = classification_router(state)
        assert route == "skip_email"
    
    def test_router_no_classification(self):
        """Test routing when no classification result."""
        state = {
            "emails": [{}],
            "current_index": 0,
            "classification_result": None
        }
        
        route = classification_router(state)
        assert route == "skip_email"
    
    def test_router_to_end_no_emails(self):
        """Test routing to END when no emails to process."""
        from langgraph.graph import END
        
        state = {
            "emails": [],
            "current_index": 0,
            "classification_result": None
        }
        
        route = classification_router(state)
        assert route == END


class TestArticleSubmissionHandler:
    """Tests for article submission handler."""
    
    @patch('nodes.handlers.RUN_CONFIG')
    def test_handle_submission_dry_run(self, mock_config, mock_email_provider, sample_email):
        """Test handling submission in dry run mode."""
        mock_config.dry_run = True
        
        with patch('nodes.handlers.PROCESSED_LABEL_ID', 'label_123'):
            state = {
                "emails": [sample_email],
                "current_email": sample_email,
                "current_index": 0,
                "processed_count": 0,
                "replied_count": 0,
                "errors": [],
                "classification_result": None
            }
            
            handler = create_article_submission_handler(mock_email_provider)
            result = handler(state)
            
            assert result["replied_count"] == 1
            assert result["processed_count"] == 1
            assert result["current_index"] == 1
            assert mock_email_provider.apply_label.called
    
    @patch('nodes.handlers.RUN_CONFIG')
    def test_handle_submission_success(self, mock_config, mock_email_provider, sample_email):
        """Test successful submission handling."""
        mock_config.dry_run = False
        
        mock_email_provider.send_reply.return_value = True
        
        with patch('nodes.handlers.PROCESSED_LABEL_ID', 'label_123'):
            state = {
                "emails": [sample_email],
                "current_email": sample_email,
                "current_index": 0,
                "processed_count": 0,
                "replied_count": 0,
                "errors": [],
                "classification_result": None
            }
            
            handler = create_article_submission_handler(mock_email_provider)
            result = handler(state)
            
            assert result["replied_count"] == 1
            assert result["processed_count"] == 1
            assert mock_email_provider.send_reply.called
            assert mock_email_provider.mark_as_read.called
            assert mock_email_provider.apply_label.called
    
    @patch('nodes.handlers.RUN_CONFIG')
    def test_handle_submission_missing_label_id(self, mock_config, mock_email_provider, sample_email):
        """Test handling submission when label ID is not configured."""
        mock_config.dry_run = False
        
        mock_email_provider.send_reply.return_value = True
        
        with patch('nodes.handlers.PROCESSED_LABEL_ID', None):
            state = {
                "emails": [sample_email],
                "current_email": sample_email,
                "current_index": 0,
                "processed_count": 0,
                "replied_count": 0,
                "errors": [],
                "classification_result": None
            }
            
            handler = create_article_submission_handler(mock_email_provider)
            result = handler(state)
            
            # Should complete successfully without applying label
            assert result["replied_count"] == 1
            assert not mock_email_provider.apply_label.called


class TestSkipHandler:
    """Tests for skip email handler."""
    
    def test_skip_email(self, mock_email_provider, sample_email, monkeypatch):
        """Test skipping an email."""
        monkeypatch.setattr('nodes.handlers.PROCESSED_LABEL_ID', 'label_123')
        
        state = {
            "emails": [sample_email],
            "current_email": sample_email,
            "current_index": 0,
            "processed_count": 0,
            "replied_count": 0,
            "errors": [],
            "classification_result": None
        }
        
        handler = create_skip_handler(mock_email_provider)
        result = handler(state)
        
        assert result["processed_count"] == 1
        assert result["replied_count"] == 0
        assert result["current_index"] == 1
        assert mock_email_provider.apply_label.called
    
    def test_skip_email_missing_label_id(self, mock_email_provider, sample_email, monkeypatch):
        """Test skipping when label ID is not configured."""
        monkeypatch.setattr('nodes.handlers.PROCESSED_LABEL_ID', None)
        
        state = {
            "emails": [sample_email],
            "current_email": sample_email,
            "current_index": 0,
            "processed_count": 0,
            "replied_count": 0,
            "errors": [],
            "classification_result": None
        }
        
        handler = create_skip_handler(mock_email_provider)
        result = handler(state)
        
        # Should complete successfully without applying label
        assert result["processed_count"] == 1
        assert not mock_email_provider.apply_label.called


class TestRouteAfterAction:
    """Tests for post-action routing."""
    
    def test_route_to_classify_more_emails(self):
        """Test routing back to classify when more emails exist."""
        state = {
            "emails": [{}, {}, {}],
            "current_index": 1
        }
        
        route = route_after_action(state)
        assert route == "classify"
    
    def test_route_to_end_no_more_emails(self):
        """Test routing to END when all emails processed."""
        from langgraph.graph import END
        
        state = {
            "emails": [{}, {}],
            "current_index": 2
        }
        
        route = route_after_action(state)
        assert route == END
