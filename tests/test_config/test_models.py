"""Tests for configuration models."""

import pytest
from lukawi.config.models import (
    AppConfig, ModelConfig, DeepSeekConfig, MockConfig,
    ToolPolicyConfig, ToolProfileConfig, MemoryConfig,
    AgentConfig, LoggingConfig, TUIConfig, DevConfig
)


class TestDeepSeekConfig:
    def test_default_values(self):
        config = DeepSeekConfig()
        assert config.api_key == ""
        assert config.model == "deepseek-v4-flash"
        assert config.base_url == "https://api.deepseek.com"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
    
    def test_custom_values(self):
        config = DeepSeekConfig(
            api_key="test-key",
            model="deepseek-v4-pro",
            temperature=0.5
        )
        assert config.api_key == "test-key"
        assert config.model == "deepseek-v4-pro"
        assert config.temperature == 0.5
    
    def test_temperature_validation(self):
        with pytest.raises(ValueError):
            DeepSeekConfig(temperature=-0.1)
        with pytest.raises(ValueError):
            DeepSeekConfig(temperature=2.1)


class TestModelConfig:
    def test_default_providers(self):
        config = ModelConfig()
        assert "deepseek" in config.providers
        assert "mock" in config.providers
        assert config.default == "deepseek"


class TestToolProfileConfig:
    def test_default_allows_all(self):
        config = ToolProfileConfig()
        assert "*" in config.allowed_tools
        assert config.denied_tools == []


class TestMemoryConfig:
    def test_default_enabled(self):
        config = MemoryConfig()
        assert config.enabled is True
        assert config.session.max_messages == 100
        assert config.longterm.enabled is True


class TestAppConfig:
    def test_default_config(self):
        config = AppConfig()
        assert config.model.default == "deepseek"
        assert config.tools.default_profile == "default"
        assert config.memory.enabled is True
        assert config.agent.max_steps == 10
        assert config.logging.level == "INFO"
        assert config.tui.theme == "lukawi-dark"
        assert config.dev.mock is False
