"""Tests for Pydantic models and type definitions."""
import pytest
from pydantic import ValidationError

from models import ClassificationResult, EmailClassification, Classification, AgentState


class TestClassificationResult:
    """Tests for ClassificationResult model (LLM response)."""
    
    def test_valid_match(self):
        """Test creating a valid classification match."""
        result = ClassificationResult(
            match=True,
            confidence=0.95,
            reasoning="Clear article submission request"
        )
        
        assert result.match is True
        assert result.confidence == 0.95
        assert result.reasoning == "Clear article submission request"
    
    def test_valid_no_match(self):
        """Test creating a valid non-match."""
        result = ClassificationResult(
            match=False,
            confidence=0.85,
            reasoning="Does not match criteria"
        )
        
        assert result.match is False
        assert result.confidence == 0.85
    
    def test_missing_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            ClassificationResult()


class TestEmailClassification:
    """Tests for EmailClassification model (final classification)."""
    
    def test_valid_classification_with_reply(self):
        """Test creating a classification with reply action."""
        classification = EmailClassification(
            classification_name="article_submission",
            confidence=0.95,
            reasoning="Test",
            action="reply",
            reply_template="templates/article_submission_reply.txt"
        )
        
        assert classification.classification_name == "article_submission"
        assert classification.action == "reply"
        assert classification.reply_template is not None
    
    def test_valid_classification_skip(self):
        """Test creating a skip classification."""
        classification = EmailClassification(
            classification_name="unclassified",
            confidence=1.0,
            reasoning="No match",
            action="skip",
            reply_template=None
        )
        
        assert classification.classification_name == "unclassified"
        assert classification.action == "skip"
        assert classification.reply_template is None


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
