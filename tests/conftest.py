"""Shared test fixtures for Lukawi Agent Framework."""

import pytest
from pathlib import Path
from lukawi.config.models import AppConfig


@pytest.fixture
def tmp_config(tmp_path):
    """Create temporary config file."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("""
model:
  default: mock
memory:
  db_path: ":memory:"
""")
    return config_path


@pytest.fixture
def app_config():
    """Default test configuration."""
    return AppConfig()


@pytest.fixture
def sample_messages():
    """Sample message list for testing."""
    from lukawi.llm.base import Message, MessageRole
    return [
        Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
        Message(role=MessageRole.USER, content="Hello!"),
    ]
