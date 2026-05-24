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
            config = AppConfig(**expanded)
            self._config = config
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return None

    @staticmethod
    def _normalize_db_path(data: dict) -> None:
        memory = data.get("memory", {})
        longterm = memory.get("longterm", {}) if isinstance(memory, dict) else {}
        db_path = longterm.get("db_path", "") if isinstance(longterm, dict) else ""
        if db_path:
            path = Path(db_path)
            if not path.is_absolute():
                longterm["db_path"] = str(Path.home() / ".lukawi" / path.name)

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

            return re.sub(pattern, replacer, data)

        elif isinstance(data, dict):
            return {
                key: self._expand_env_vars(value)
                for key, value in data.items()
            }

        elif isinstance(data, list):
            return [self._expand_env_vars(item) for item in data]

        return data


def load_config(config_path: str | Path | None = None) -> AppConfig:
    load_dotenv()
    settings = Settings(config_path)
    return settings.load()
