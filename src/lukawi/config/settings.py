from __future__ import annotations

import importlib.resources as resources
import os
import re
from pathlib import Path
from typing import Any

import logging

import yaml
from dotenv import load_dotenv

from lukawi.config.models import AppConfig

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _get_default_config_path() -> Path:
    """Resolve the bundled default config path.
    
    Uses importlib.resources to find the config bundled inside the package,
    falling back to dev-mode project-root path for editable installs.
    """
    try:
        ref = resources.files("lukawi.data") / "default.yaml"
        return Path(str(ref))
    except (TypeError, ModuleNotFoundError, FileNotFoundError):
        return Path(__file__).parent.parent.parent.parent / "config" / "default.yaml"


DEFAULT_CONFIG_PATH = _get_default_config_path()


class Settings:
    def __init__(self, config_path: str | Path | None = None):
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self._config: AppConfig | None = None

    def load(self) -> AppConfig | None:
        try:
            raw = self._load_yaml(self.config_path)
            expanded = self._expand_env_vars(raw) if raw else {}
            self._normalize_db_path(expanded)
            
            # Add custom model from environment variables if configured
            self._add_custom_model_from_env(expanded)
            
            config = AppConfig(**expanded)
            self._config = config
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return None

    @staticmethod
    def _normalize_db_path(data: dict) -> None:
        """Normalize relative db_path and chroma_db_dir to absolute paths under ~/.lukawi/."""
        memory = data.get("memory", {})
        longterm = memory.get("longterm", {}) if isinstance(memory, dict) else {}
        db_path = longterm.get("db_path", "") if isinstance(longterm, dict) else ""
        if db_path:
            path = Path(db_path)
            if not path.is_absolute():
                longterm["db_path"] = str(Path.home() / ".lukawi" / path.name)

        rag = data.get("rag", {})
        chroma_dir = rag.get("chroma_db_dir", "") if isinstance(rag, dict) else ""
        if chroma_dir:
            path = Path(chroma_dir)
            if not path.is_absolute():
                rag["chroma_db_dir"] = str(Path.home() / ".lukawi" / path.name)

    @staticmethod
    def _add_custom_model_from_env(data: dict) -> None:
        """Add custom model configuration from environment variables."""
        import os
        
        custom_model_id = os.environ.get("CUSTOM_MODEL_ID", "")
        custom_model_base_url = os.environ.get("CUSTOM_MODEL_BASE_URL", "")
        custom_model_api_key = os.environ.get("CUSTOM_MODEL_API_KEY", "")
        
        if custom_model_id and custom_model_base_url and custom_model_api_key:
            # Ensure model.providers exists
            if "model" not in data:
                data["model"] = {}
            if "providers" not in data["model"]:
                data["model"]["providers"] = {}
            
            # Add custom model to providers
            custom_model_name = os.environ.get("CUSTOM_MODEL_NAME", custom_model_id)
            data["model"]["providers"][custom_model_name] = {
                "type": "custom",
                "api_key": custom_model_api_key,
                "model": custom_model_id,
                "base_url": custom_model_base_url,
                "max_tokens": 4096,
                "temperature": 0.7,
                "name": custom_model_name,
            }

    def get(self) -> AppConfig:
        if self._config is None:
            self._config = self.load()
        return self._config

    def reload(self) -> AppConfig:
        self._config = None
        return self.load()

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return data if data else {}

    def _expand_env_vars(self, data: Any) -> Any:
        if isinstance(data, str):
            pattern = r'\$\{([^}]+)\}'

            def replacer(match: re.Match[str]) -> str:
                var_name = match.group(1)
                value = os.environ.get(var_name, "")
                return value

            result = re.sub(pattern, replacer, data)
            # Expand ~ to user home directory
            if result.startswith("~/"):
                result = str(Path.home() / result[2:])
            elif result == "~":
                result = str(Path.home())
            return result

        elif isinstance(data, dict):
            return {
                key: self._expand_env_vars(value)
                for key, value in data.items()
            }

        elif isinstance(data, list):
            return [self._expand_env_vars(item) for item in data]

        return data


def load_config(config_path: str | Path | None = None) -> AppConfig:
    load_dotenv(dotenv_path=Path.home() / ".lukawi" / ".env", override=True)
    settings = Settings(config_path)
    return settings.load()
