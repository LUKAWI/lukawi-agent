import pytest
import os
from pathlib import Path

from lukawi.config.settings import Settings, load_config
from lukawi.config.models import AppConfig


class TestSettings:
    def test_load_default_config(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
model:
  default: deepseek
  providers:
    deepseek:
      api_key: test-key
""")
        settings = Settings(config_file)
        config = settings.load()

        assert isinstance(config, AppConfig)
        assert config.model.default == "deepseek"

    def test_expand_env_vars(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TEST_API_KEY", "my-secret-key")

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
model:
  providers:
    deepseek:
      api_key: ${TEST_API_KEY}
""")
        settings = Settings(config_file)
        config = settings.load()

        assert config.model.providers["deepseek"].api_key == "my-secret-key"

    def test_missing_file_returns_none(self):
        settings = Settings("/nonexistent/config.yaml")
        result = settings.load()
        assert result is None

    def test_lazy_loading(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("model:\n  default: mock")

        settings = Settings(config_file)
        assert settings._config is None

        config = settings.get()
        assert settings._config is not None
        assert config.model.default == "mock"

    def test_reload(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("model:\n  default: deepseek")

        settings = Settings(config_file)
        config1 = settings.load()
        assert config1.model.default == "deepseek"

        config_file.write_text("model:\n  default: mock")
        config2 = settings.reload()
        assert config2.model.default == "mock"


class TestLoadConfig:
    def test_convenience_function(self, tmp_path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("model:\n  default: mock")

        config = load_config(config_file)
        assert isinstance(config, AppConfig)
        assert config.model.default == "mock"
