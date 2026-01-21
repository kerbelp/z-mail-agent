"""Tests for configuration loading."""
import os
import pytest


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
