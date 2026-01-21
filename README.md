# z-mail-agent

![Banner](assets/z-mail-agent.jpg)

An intelligent email assistant powered by LangGraph and LLMs that automatically processes and responds to article submission requests.

## Overview

This email assistant automatically:
- Fetches unread emails from your inbox
- Classifies them using GPT-4o to identify article submission requests
- Sends automated responses to genuine submission requests
- Labels processed emails to avoid duplicate processing
- Provides detailed logging and error handling

## Architecture

The codebase is organized into modular components for easy maintenance and extensibility:

```
z-mail-agent/
├── main.py                 # Entry point with LangGraph workflow
├── config.py              # Configuration management
├── models.py              # Type definitions (Pydantic models, AgentState)
├── email_providers/       # Email provider implementations
│   ├── __init__.py
│   ├── base.py           # Abstract EmailProvider interface
│   └── zoho.py           # Zoho Mail implementation
└── nodes/                 # LangGraph workflow nodes
    ├── __init__.py
    ├── ingest.py         # Email ingestion node
    ├── classify.py       # Email classification with LLM
    └── handlers.py       # Action handlers (reply, skip)
```

### Key Components

#### Email Provider Interface

The `EmailProvider` abstract base class in [email_providers/base.py](email_providers/base.py) defines a standard interface for email operations:

```python
class EmailProvider(ABC):
    @abstractmethod
    def fetch_unread_emails(self, limit: int, exclude_label_id: Optional[str] = None) -> List[Dict]:
        """Fetch unread emails, optionally excluding those with a specific label."""
        
    @abstractmethod
    def get_email_content(self, message_id: str, folder_id: str) -> str:
        """Retrieve the full content of an email."""
        
    @abstractmethod
    def send_reply(self, message_id: str, to_address: str, subject: str, content: str) -> bool:
        """Send a reply email."""
        
    @abstractmethod
    def mark_as_read(self, message_id: str) -> bool:
        """Mark an email as read."""
        
    @abstractmethod
    def apply_label(self, message_id: str, folder_id: str, label_id: str) -> bool:
        """Apply a label to an email."""
```

This design allows you to easily add support for other email providers (Gmail, Outlook, etc.) by implementing these 5 methods.

#### LangGraph Workflow

The workflow follows this sequence:

1. **Ingest** - Fetch unread emails (excluding already processed ones)
2. **Classify** - Use LLM to identify article submission requests
3. **Handle/Skip** - Send automated reply or skip based on classification
4. **Loop** - Process next email or end workflow

Each node is created using factory functions that accept an `EmailProvider` instance, enabling dependency injection and testability.

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd z-mail-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables (copy from `.env.example`):
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

Configure the assistant using environment variables in your `.env` file:

```bash
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# Zoho Mail Configuration
ZOHO_MCP_URL=http://localhost:3000
ZOHO_ACCOUNT_ID=your_account_id
REPLY_EMAIL_ADDRESS=your_email@domain.com

# Behavior flags
DEBUG=false           # Enable debug logging
DRY_RUN=false        # Log actions without executing
SEND_REPLY=true      # Send email replies
ADD_LABEL=true       # Apply labels to processed emails
```

### Configuration Flags

- **DEBUG**: When `true`, logs detailed API request/response information
- **DRY_RUN**: When `true`, simulates actions without actually sending emails or modifying data
- **SEND_REPLY**: Controls whether to send automated replies (only relevant when `DRY_RUN=false`)
- **ADD_LABEL**: Controls whether to apply labels to processed emails

## Usage

Run the assistant:

```bash
python main.py
```

The assistant will:
1. Fetch unread emails from your inbox
2. Filter out already-processed emails (those with the "processed by z-mail-agent" label)
3. Classify each email to identify article submission requests
4. Send automated responses to genuine requests
5. Apply labels to all processed emails
6. Display a summary of actions taken

## Adding New Email Providers

To add support for a new email provider (e.g., Gmail):

1. Create a new file in the `email_providers/` directory (e.g., `gmail.py`)
2. Implement the `EmailProvider` interface:

```python
from email_providers.base import EmailProvider
from typing import List, Dict, Optional

class GmailEmailProvider(EmailProvider):
    def __init__(self):
        # Initialize Gmail API client
        pass
    
    def fetch_unread_emails(self, limit: int, exclude_label_id: Optional[str] = None) -> List[Dict]:
        # Implement using Gmail API
        pass
    
    def get_email_content(self, message_id: str, folder_id: str) -> str:
        # Implement using Gmail API
        pass
    
    def send_reply(self, message_id: str, to_address: str, subject: str, content: str) -> bool:
        # Implement using Gmail API
        pass
    
    def mark_as_read(self, message_id: str) -> bool:
        # Implement using Gmail API
        pass
    
    def apply_label(self, message_id: str, folder_id: str, label_id: str) -> bool:
        # Implement using Gmail API
        pass
```

3. Update `email_providers/__init__.py` to export your new provider:
```python
from email_providers.gmail import GmailEmailProvider
```

4. Update `main.py` to use your provider:
```python
# Replace ZohoEmailProvider with your provider
email_provider = GmailEmailProvider()
```

## Development

### Project Structure

- **config.py**: Centralized configuration using Pydantic models
- **models.py**: Type definitions for LangGraph state and LLM output
- **email_providers/base.py**: Abstract interface for email operations
- **email_providers/zoho.py**: Zoho Mail implementation via MCP
- **nodes/**: LangGraph workflow nodes with factory functions
- **main.py**: Workflow construction and execution

### Testing

#### Unit Tests

The project includes comprehensive unit tests covering:
- Configuration loading and validation
- Email provider implementations
- Workflow nodes and routing logic
- State management

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_config.py -v

# Run tests matching pattern
pytest -k "test_email" -v
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

#### Manual Testing

Run in dry-run mode to test without sending emails:

```bash
DEBUG=true DRY_RUN=true python main.py
```

Test with labeling only (no replies):

```bash
SEND_REPLY=false ADD_LABEL=true python main.py
```

## Contributing

Contributions are welcome! Areas for improvement:

1. **Email Providers**: Implement support for Gmail, Outlook, etc.
2. **Classification**: Enhance LLM prompts for better accuracy
3. **Handlers**: Add new email categories and automated responses
4. **Testing**: Expand test coverage and add integration tests
5. **Documentation**: Improve setup guides and examples

When contributing, please:
- Add unit tests for new features
- Ensure all tests pass (`pytest`)
- Follow existing code style
- Update documentation as needed

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues and questions, please open an issue on GitHub.
