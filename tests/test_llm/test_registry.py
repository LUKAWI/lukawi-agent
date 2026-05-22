"""Tests for model registry."""

import pytest
from lukawi.llm.registry import ModelRegistry, ModelNotFoundError
from lukawi.llm.mock import MockProvider
from lukawi.llm.base import ModelInfo
from lukawi.config.models import ModelConfig, DeepSeekConfig, MockConfig


@pytest.fixture
def registry():
    return ModelRegistry()


@pytest.fixture
def mock_provider():
    return MockProvider()


class TestModelRegistry:
    def test_register(self, registry, mock_provider):
        registry.register("mock", mock_provider)

        assert registry.has("mock")
        assert registry.current == mock_provider

    def test_register_duplicate_raises(self, registry, mock_provider):
        registry.register("mock", mock_provider)

        with pytest.raises(ValueError, match="already registered"):
            registry.register("mock", mock_provider)

    def test_use(self, registry, mock_provider):
        registry.register("mock", mock_provider)
        registry.use("mock")

        assert registry.current_name == "mock"

    def test_use_nonexistent_raises(self, registry):
        with pytest.raises(ModelNotFoundError):
            registry.use("nonexistent")

    def test_current_no_providers(self, registry):
        with pytest.raises(RuntimeError, match="No providers"):
            _ = registry.current

    def test_get(self, registry, mock_provider):
        registry.register("mock", mock_provider)

        assert registry.get("mock") == mock_provider

    def test_get_nonexistent_raises(self, registry):
        with pytest.raises(ModelNotFoundError):
            registry.get("nonexistent")

    def test_list_models(self, registry, mock_provider):
        registry.register("mock", mock_provider)

        models = registry.list_models()
        assert len(models) == 1
        assert models[0].name == "mock"

    def test_has(self, registry, mock_provider):
        assert not registry.has("mock")
        registry.register("mock", mock_provider)
        assert registry.has("mock")

    def test_from_config(self):
        config = ModelConfig(
            default="mock",
            providers={"mock": MockConfig()},
        )

        registry = ModelRegistry.from_config(config)

        assert registry.has("mock")
        assert registry.current_name == "mock"
        assert isinstance(registry.current, MockProvider)
