"""Configuration management for the email assistant."""
import os
import sys
import logging
from pydantic import BaseModel, ConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log output when in a terminal."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    
    # Special colors for specific messages
    SPECIAL_COLORS = {
        'article_submission': '\033[1;32m',  # Bold Green
        'skip': '\033[90m',                  # Gray
        'dry_run': '\033[1;33m',             # Bold Yellow
        'success': '\033[1;32m',             # Bold Green
    }
    
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def __init__(self, *args, use_color=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_color = use_color and sys.stdout.isatty()
    
    def format(self, record):
        if not self.use_color:
            return super().format(record)
        
        # Apply color based on log level
        levelname_color = self.COLORS.get(record.levelname, '')
        
        # Check for special message patterns
        message = record.getMessage()
        message_color = ''
        
        if 'article submission' in message.lower() or 'handling article' in message.lower():
            message_color = self.SPECIAL_COLORS['article_submission']
        elif 'skipping' in message.lower():
            message_color = self.SPECIAL_COLORS['skip']
        elif '[DRY RUN]' in message or 'dry_run' in message.lower():
            message_color = self.SPECIAL_COLORS['dry_run']
        elif 'sent reply' in message.lower() or 'applied label' in message.lower():
            message_color = self.SPECIAL_COLORS['success']
        
        # Format the record
        formatted = super().format(record)
        
        # Apply colors
        if message_color:
            return f"{message_color}{formatted}{self.RESET}"
        else:
            return f"{levelname_color}{formatted}{self.RESET}"


def setup_logging():
    """Configure logging with colors if terminal supports it."""
    use_color = os.getenv("NO_COLOR") is None  # Respect NO_COLOR env var
    
    formatter = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        use_color=use_color
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    # Suppress retry logs from httpx and openai libraries
    # These create noise during rate limit retries
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("openai").setLevel(logging.ERROR)
    logging.getLogger("httpcore").setLevel(logging.ERROR)


# Setup logging before anything else
setup_logging()


class RunConfig(BaseModel):
    """Configuration for email processing behavior."""
    model_config = ConfigDict(frozen=True)
    
    debug: bool = False  # If True, logs debug information from API calls
    dry_run: bool = False  # If True, logs actions without executing
    send_reply: bool = True  # If True, sends email replies (only relevant when dry_run=False)
    add_label: bool = True  # If True, applies labels to processed emails


# Create config instance from environment or use defaults
RUN_CONFIG = RunConfig(
    debug=os.getenv("DEBUG", "False").lower() == "true",
    dry_run=os.getenv("DRY_RUN", "False").lower() == "true",
    send_reply=os.getenv("SEND_REPLY", "True").lower() == "true",
    add_label=os.getenv("ADD_LABEL", "True").lower() == "true"
)

# Email processing settings
READ_EMAIL_LIMIT = int(os.getenv("READ_EMAIL_LIMIT", "10"))
READ_EMAIL_STATUS = "unread"
PROCESSED_LABEL = "processed by AIEA"
REPLY_EMAIL_ADDRESS = os.getenv("REPLY_EMAIL_ADDRESS")

# Zoho-specific configuration
ZOHO_MCP_URL = os.getenv("ZOHO_MCP_URL")
ZOHO_ACCOUNT_ID = os.getenv("ZOHO_ACCOUNT_ID")

# Generic label ID for processed emails (provider-agnostic)
PROCESSED_LABEL_ID = os.getenv("ZOHO_PROCESSED_LABEL_ID")

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()  # openai, anthropic, etc.
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")  # Model name
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))  # Temperature (0-1)
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")  # API key (fallback to OPENAI_API_KEY)

# Legacy: Keep for backwards compatibility
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
