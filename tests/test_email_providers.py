"""Tests for email provider implementations."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from email_providers.zoho import ZohoEmailProvider


class TestZohoEmailProvider:
    """Tests for Zoho email provider."""
    
    @pytest.fixture
    def provider(self, monkeypatch):
        """Create a Zoho provider with mocked config."""
        monkeypatch.setenv("ZOHO_MCP_URL", "http://test.local")
        monkeypatch.setenv("ZOHO_ACCOUNT_ID", "test_account")
        monkeypatch.setenv("REPLY_EMAIL_ADDRESS", "test@example.com")
        
        # Reload config module first to pick up mocked env vars
        import importlib
        import config
        importlib.reload(config)
        
        # Then reload zoho provider to use new config values
        import email_providers.zoho
        importlib.reload(email_providers.zoho)
        from email_providers.zoho import ZohoEmailProvider
        
        return ZohoEmailProvider()
    
    def test_initialization(self, provider):
        """Test provider initialization."""
        assert provider.mcp_url == "http://test.local"
        assert provider.account_id == "test_account"
        assert provider.reply_from_address == "test@example.com"
        assert provider.timeout == 10
    
    @patch('email_providers.zoho.requests.post')
    def test_fetch_unread_emails_success(self, mock_post, provider):
        """Test successful email fetching."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'result': {
                'content': [{
                    'text': json.dumps({
                        'data': [
                            {'messageId': '123', 'subject': 'Test', 'labelId': []},
                            {'messageId': '456', 'subject': 'Test 2', 'labelId': []}
                        ]
                    })
                }]
            }
        }
        mock_post.return_value = mock_response
        
        emails = provider.fetch_unread_emails(limit=10)
        
        assert len(emails) == 2
        assert emails[0]['messageId'] == '123'
        assert mock_post.called
    
    @patch('email_providers.zoho.requests.post')
    def test_fetch_unread_emails_with_label_filter(self, mock_post, provider):
        """Test email fetching with label filtering."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'result': {
                'content': [{
                    'text': json.dumps({
                        'data': [
                            {'messageId': '123', 'subject': 'Test', 'labelId': []},
                            {'messageId': '456', 'subject': 'Test 2', 'labelId': ['processed']},
                            {'messageId': '789', 'subject': 'Test 3', 'labelId': []}
                        ]
                    })
                }]
            }
        }
        mock_post.return_value = mock_response
        
        emails = provider.fetch_unread_emails(limit=10, exclude_label_id='processed')
        
        assert len(emails) == 2
        assert all('processed' not in email.get('labelId', []) for email in emails)
    
    @patch('email_providers.zoho.requests.post')
    def test_fetch_unread_emails_fetches_3x_limit_when_filtering(self, mock_post, provider):
        """Test that fetch limit is multiplied by 3 when filtering by label."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'result': {
                'content': [{
                    'text': json.dumps({'data': []})
                }]
            }
        }
        mock_post.return_value = mock_response
        
        provider.fetch_unread_emails(limit=10, exclude_label_id='processed')
        
        # Check the API was called with limit=30
        call_args = mock_post.call_args
        request_data = call_args[1]['json']
        assert request_data['params']['arguments']['query_params']['limit'] == 30
    
    @patch('email_providers.zoho.requests.post')
    def test_get_email_content_success(self, mock_post, provider):
        """Test successful email content retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'result': {
                'content': [{
                    'text': json.dumps({
                        'data': {'content': 'Email body content'}
                    })
                }]
            }
        }
        mock_post.return_value = mock_response
        
        content = provider.get_email_content('123', '789')
        
        assert content == 'Email body content'
    
    def test_get_email_content_missing_params(self, provider):
        """Test email content retrieval with missing parameters."""
        content = provider.get_email_content(None, '789')
        assert content == ""
        
        content = provider.get_email_content('123', None)
        assert content == ""
    
    @patch('email_providers.zoho.requests.post')
    @patch('email_providers.zoho.RUN_CONFIG')
    def test_send_reply_success(self, mock_config, mock_post, provider):
        """Test successful reply sending."""
        mock_config.dry_run = False
        mock_config.send_reply = True
        
        mock_response = Mock()
        mock_response.json.return_value = {'result': {}}
        mock_post.return_value = mock_response
        
        result = provider.send_reply('123', 'to@example.com', 'Subject', 'Content')
        
        assert result is True
        assert mock_post.called
    
    def test_send_reply_missing_params(self, provider):
        """Test reply sending with missing parameters."""
        result = provider.send_reply(None, 'to@example.com', 'Subject', 'Content')
        assert result is False
        
        result = provider.send_reply('123', None, 'Subject', 'Content')
        assert result is False
    
    @patch('email_providers.zoho.requests.post')
    @patch('email_providers.zoho.RUN_CONFIG')
    def test_mark_as_read_success(self, mock_config, mock_post, provider):
        """Test successful mark as read."""
        mock_config.dry_run = False
        
        mock_response = Mock()
        mock_response.json.return_value = {'result': {}}
        mock_post.return_value = mock_response
        
        result = provider.mark_as_read('123')
        
        assert result is True
        assert mock_post.called
    
    def test_mark_as_read_missing_message_id(self, provider):
        """Test mark as read with missing message ID."""
        result = provider.mark_as_read(None)
        assert result is False
    
    @patch('email_providers.zoho.requests.post')
    @patch('email_providers.zoho.RUN_CONFIG')
    def test_apply_label_success(self, mock_config, mock_post, provider):
        """Test successful label application."""
        mock_config.dry_run = False
        mock_config.add_label = True
        
        mock_response = Mock()
        mock_response.json.return_value = {'result': {'isError': False}}
        mock_post.return_value = mock_response
        
        result = provider.apply_label('123', '789', 'label_id')
        
        assert result is True
        assert mock_post.called
    
    def test_apply_label_missing_params(self, provider):
        """Test label application with missing parameters."""
        result = provider.apply_label(None, '789', 'label_id')
        assert result is False
        
        result = provider.apply_label('123', None, 'label_id')
        assert result is False
        
        result = provider.apply_label('123', '789', None)
        assert result is False
    
    @patch('email_providers.zoho.requests.post')
    @patch('email_providers.zoho.RUN_CONFIG')
    def test_apply_label_api_error(self, mock_config, mock_post, provider):
        """Test label application when API returns error."""
        mock_config.dry_run = False
        mock_config.add_label = True
        
        mock_response = Mock()
        mock_response.json.return_value = {'result': {'isError': True}}
        mock_post.return_value = mock_response
        
        result = provider.apply_label('123', '789', 'label_id')
        
        assert result is False
