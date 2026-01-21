"""Tests for Pydantic models and type definitions."""
import pytest
from pydantic import ValidationError

from models import SubmissionCheck, AgentState


class TestSubmissionCheck:
    """Tests for SubmissionCheck model."""
    
    def test_valid_article_submission(self):
        """Test creating a valid article submission classification."""
        check = SubmissionCheck(
            is_article_submission=True,
            email_type="article_submission"
        )
        
        assert check.is_article_submission is True
        assert check.email_type == "article_submission"
    
    def test_valid_other_type(self):
        """Test creating a valid 'other' classification."""
        check = SubmissionCheck(
            is_article_submission=False,
            email_type="other"
        )
        
        assert check.is_article_submission is False
        assert check.email_type == "other"
    
    def test_missing_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            SubmissionCheck()


class TestAgentState:
    """Tests for AgentState type definition."""
    
    def test_agent_state_structure(self):
        """Test AgentState has all required fields."""
        # AgentState is a TypedDict, so we just verify we can import it
        # and it has the expected structure
        assert hasattr(AgentState, '__annotations__')
        
        expected_fields = {
            'emails', 'processed_count', 'replied_count',
            'current_index', 'errors', 'current_email',
            'classification_result'
        }
        
        actual_fields = set(AgentState.__annotations__.keys())
        assert expected_fields == actual_fields
