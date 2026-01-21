"""Pytest configuration and shared fixtures."""
import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, List

from email_providers.base import EmailProvider


@pytest.fixture
def mock_email_provider():
    """Create a mock email provider for testing."""
    provider = Mock(spec=EmailProvider)
    provider.fetch_unread_emails.return_value = []
    provider.get_email_content.return_value = "Test email content"
    provider.send_reply.return_value = True
    provider.mark_as_read.return_value = True
    provider.apply_label.return_value = True
    return provider


@pytest.fixture
def sample_email():
    """Create a sample email for testing."""
    return {
        "messageId": "123456",
        "folderId": "789",
        "subject": "Test Article Submission",
        "fromAddress": "test@example.com",
        "toAddress": "pavel@ai-collection.org",
        "summary": "I would like to submit an article",
        "labelId": []
    }


@pytest.fixture
def sample_emails():
    """Create a list of sample emails for testing."""
    return [
        {
            "messageId": "123456",
            "folderId": "789",
            "subject": "Article Submission Request",
            "fromAddress": "author1@example.com",
            "summary": "I would like to submit a guest post",
            "labelId": []
        },
        {
            "messageId": "234567",
            "folderId": "789",
            "subject": "Newsletter",
            "fromAddress": "news@example.com",
            "summary": "Weekly newsletter",
            "labelId": []
        }
    ]


@pytest.fixture
def initial_state():
    """Create initial agent state for testing."""
    return {
        "emails": [],
        "processed_count": 0,
        "replied_count": 0,
        "current_index": 0,
        "errors": [],
        "current_email": {},
        "classification_result": None
    }
