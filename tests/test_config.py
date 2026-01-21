"""Tests for configuration loading."""
import os
import pytest
import tempfile
from pathlib import Path


def test_reply_template_from_env(monkeypatch):
    """Test loading reply template from environment variable."""
    test_template = "Custom template from env"
    monkeypatch.setenv("REPLY_TEMPLATE", test_template)
    
    # Reload config module to pick up new env var
    import importlib
    import config
    importlib.reload(config)
    
    assert config.REPLY_TEMPLATE == test_template


def test_reply_template_from_file(monkeypatch, tmp_path):
    """Test loading reply template from file."""
    # Clear environment variable
    monkeypatch.delenv("REPLY_TEMPLATE", raising=False)
    
    # Create temporary template files
    template_content = "Template from file"
    template_file = tmp_path / "reply_template.txt"
    template_file.write_text(template_content)
    
    classification_content = "Classification prompt from file"
    classification_file = tmp_path / "classification_prompt.txt"
    classification_file.write_text(classification_content)
    
    # Mock the file path
    monkeypatch.setattr("config.os.path.dirname", lambda x: str(tmp_path))
    
    # Reload config
    import importlib
    import config
    importlib.reload(config)
    
    assert config.REPLY_TEMPLATE == template_content
    assert config.CLASSIFICATION_PROMPT == classification_content


def test_reply_template_missing_raises_error(monkeypatch, tmp_path):
    """Test that missing reply template raises ValueError."""
    # Clear environment variable
    monkeypatch.delenv("REPLY_TEMPLATE", raising=False)
    
    # Create classification prompt so only reply template is missing
    classification_file = tmp_path / "classification_prompt.txt"
    classification_file.write_text("Test prompt")
    
    # Mock the file path to non-existent location
    monkeypatch.setattr("config.os.path.dirname", lambda x: str(tmp_path))
    
    # Reload config should raise ValueError
    with pytest.raises(ValueError, match="REPLY_TEMPLATE is not configured"):
        import importlib
        import config
        importlib.reload(config)


def test_classification_prompt_from_env(monkeypatch):
    """Test loading classification prompt from environment variable."""
    prompt_content = "Test classification prompt"
    monkeypatch.setenv("CLASSIFICATION_PROMPT", prompt_content)
    monkeypatch.setenv("REPLY_TEMPLATE", "Test template")
    
    # Reload config
    import importlib
    import config
    importlib.reload(config)
    
    assert config.CLASSIFICATION_PROMPT == prompt_content


def test_classification_prompt_from_file(monkeypatch, tmp_path):
    """Test loading classification prompt from file."""
    # Clear environment variable
    monkeypatch.delenv("CLASSIFICATION_PROMPT", raising=False)
    
    # Create temporary files
    prompt_content = "Prompt from file"
    prompt_file = tmp_path / "classification_prompt.txt"
    prompt_file.write_text(prompt_content)
    
    template_file = tmp_path / "reply_template.txt"
    template_file.write_text("Test template")
    
    # Mock the file path
    monkeypatch.setattr("config.os.path.dirname", lambda x: str(tmp_path))
    
    # Reload config
    import importlib
    import config
    importlib.reload(config)
    
    assert config.CLASSIFICATION_PROMPT == prompt_content


def test_classification_prompt_missing_raises_error(monkeypatch, tmp_path):
    """Test that missing classification prompt raises ValueError."""
    # Clear environment variable
    monkeypatch.delenv("CLASSIFICATION_PROMPT", raising=False)
    
    # Create reply template so only classification prompt is missing
    template_file = tmp_path / "reply_template.txt"
    template_file.write_text("Test template")
    
    # Mock the file path to non-existent location
    monkeypatch.setattr("config.os.path.dirname", lambda x: str(tmp_path))
    
    # Reload config should raise ValueError
    with pytest.raises(ValueError, match="CLASSIFICATION_PROMPT is not configured"):
        import importlib
        import config
        importlib.reload(config)


def test_run_config_defaults():
    """Test RunConfig default values."""
    from config import RunConfig
    
    config = RunConfig()
    assert config.debug is False
    assert config.dry_run is False
    assert config.send_reply is True
    assert config.add_label is True


def test_run_config_from_env(monkeypatch):
    """Test RunConfig loading from environment variables."""
    from config import RunConfig
    
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DRY_RUN", "true")
    monkeypatch.setenv("SEND_REPLY", "false")
    monkeypatch.setenv("ADD_LABEL", "false")
    
    config = RunConfig(
        debug=os.getenv("DEBUG", "False").lower() == "true",
        dry_run=os.getenv("DRY_RUN", "False").lower() == "true",
        send_reply=os.getenv("SEND_REPLY", "True").lower() == "true",
        add_label=os.getenv("ADD_LABEL", "True").lower() == "true"
    )
    
    assert config.debug is True
    assert config.dry_run is True
    assert config.send_reply is False
    assert config.add_label is False


def test_run_config_is_immutable():
    """Test that RunConfig is immutable (frozen)."""
    from config import RunConfig
    
    config = RunConfig()
    
    with pytest.raises(Exception):  # Pydantic raises ValidationError
        config.debug = True


def test_read_email_limit_from_env(monkeypatch):
    """Test READ_EMAIL_LIMIT loading from environment."""
    monkeypatch.setenv("READ_EMAIL_LIMIT", "25")
    
    import importlib
    import config
    importlib.reload(config)
    
    assert config.READ_EMAIL_LIMIT == 25


def test_read_email_limit_default(monkeypatch):
    """Test READ_EMAIL_LIMIT default value."""
    monkeypatch.delenv("READ_EMAIL_LIMIT", raising=False)
    
    import importlib
    import config
    importlib.reload(config)
    
    assert config.READ_EMAIL_LIMIT == 10
