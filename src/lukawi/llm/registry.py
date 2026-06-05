"""Model registry for managing LLM providers."""

from __future__ import annotations

from lukawi.llm.base import LLMProvider, ModelInfo
from lukawi.config.models import ModelConfig, DeepSeekConfig, CustomModelConfig, MockConfig


class ModelNotFoundError(Exception):
    """Raised when a requested model is not found."""


class ModelRegistry:
    """Registry for managing multiple LLM providers."""

    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}
        self._current_name: str | None = None

    def register(self, name: str, provider: LLMProvider) -> None:
        if name in self._providers:
            raise ValueError(f"Provider '{name}' already registered")

        self._providers[name] = provider

        if self._current_name is None:
            self._current_name = name

    def use(self, name: str) -> None:
        if name not in self._providers:
            raise ModelNotFoundError(f"Provider '{name}' not found")

        self._current_name = name

    @property
    def current(self) -> LLMProvider:
        if not self._current_name:
            raise RuntimeError("No providers registered")

        return self._providers[self._current_name]

    @property
    def current_name(self) -> str | None:
        return self._current_name

    def get(self, name: str) -> LLMProvider:
        if name not in self._providers:
            raise ModelNotFoundError(f"Provider '{name}' not found")

        return self._providers[name]

    def list_models(self) -> list[ModelInfo]:
        return [
            provider.get_model_info()
            for provider in self._providers.values()
        ]

    def list_registered(self) -> list[tuple[str, ModelInfo]]:
        """List all registered models with their registry key and info.

        Returns:
            List of (registry_key, ModelInfo) tuples
        """
        return [
            (name, provider.get_model_info())
            for name, provider in self._providers.items()
        ]

    def has(self, name: str) -> bool:
        return name in self._providers

    @classmethod
    def from_config(cls, config: ModelConfig) -> ModelRegistry:
        registry = cls()

        for name, provider_config in config.providers.items():
            if isinstance(provider_config, DeepSeekConfig):
                if not provider_config.api_key:
                    continue
                from lukawi.llm.deepseek import DeepSeekProvider
                provider = DeepSeekProvider(provider_config)
            elif isinstance(provider_config, CustomModelConfig):
                if not provider_config.api_key:
                    continue
                from lukawi.llm.deepseek import DeepSeekProvider
                provider = DeepSeekProvider(provider_config)
            elif isinstance(provider_config, MockConfig):
                from lukawi.llm.mock import MockProvider
                provider = MockProvider()
            else:
                continue

            registry.register(name, provider)

        if config.default:
            registry.use(config.default)

        return registry
