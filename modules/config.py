"""Configuration helpers for WaterlooWorks automation."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Mapping, MutableMapping, Optional, Tuple

try:  # Optional dependency so tests don't require python-dotenv
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback when dependency is missing
    def load_dotenv(*args, **kwargs):  # type: ignore[override]
        return False

_env_loaded = False
_config_cache: Dict[str, "AppConfig"] = {}


def load_environment(dotenv_path: Optional[str] = None, *, override: bool = False) -> None:
    """Ensure environment variables from a .env file are loaded once."""
    global _env_loaded

    if _env_loaded and dotenv_path is None:
        return

    load_dotenv(dotenv_path=dotenv_path, override=override)
    _env_loaded = True


def get_waterlooworks_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Retrieve WaterlooWorks credentials from the environment."""
    load_environment()
    return os.getenv("WATERLOOWORKS_USERNAME"), os.getenv("WATERLOOWORKS_PASSWORD")


def resolve_waterlooworks_credentials(
    username: Optional[str] = None,
    password: Optional[str] = None,
    *,
    require: bool = False,
) -> Tuple[Optional[str], Optional[str]]:
    """Resolve credentials by preferring explicit arguments over configuration."""

    env_username, env_password = get_waterlooworks_credentials()

    resolved_username = username or env_username
    resolved_password = password or env_password

    if require and (not resolved_username or not resolved_password):
        raise RuntimeError(
            "WaterlooWorks credentials are not configured. Set WATERLOOWORKS_USERNAME "
            "and WATERLOOWORKS_PASSWORD in your environment or .env file."
        )

    return resolved_username, resolved_password


@dataclass
class MatcherSettings:
    """Structured access to matcher configuration."""

    data: MutableMapping[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    @property
    def embedding_model(self) -> Optional[str]:
        return self.data.get("embedding_model")

    @property
    def auto_save_threshold(self) -> int:
        return self.data.get("auto_save_threshold", 30)

    @property
    def llm_provider(self) -> str:
        return self.data.get("llm_provider", "gemini")

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.data)


class AppConfig(Mapping[str, Any]):
    """Wrapper around configuration data with convenience helpers."""

    def __init__(self, data: MutableMapping[str, Any], source_path: Optional[str] = None):
        self._data = data
        self._source_path = source_path
        self.matcher = MatcherSettings(data.get("matcher", {}))

    @property
    def resume_path(self) -> str:
        return self._data.get("resume_path", "input/resume.pdf")

    @property
    def explicit_skills(self) -> MutableMapping[str, Any]:
        return self._data.get("explicit_skills", {})

    @property
    def source_path(self) -> Optional[str]:
        return self._source_path

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self._data)


def load_app_config(config_path: str = "config.json") -> AppConfig:
    """Load configuration once and expose it as a structured object."""

    absolute_path = os.path.abspath(config_path)
    cached = _config_cache.get(absolute_path)
    if cached:
        return cached

    with open(absolute_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    config = AppConfig(data, source_path=absolute_path)
    _config_cache[absolute_path] = config
    return config


def app_config_from_dict(data: MutableMapping[str, Any], *, source_path: Optional[str] = None) -> AppConfig:
    """Build an :class:`AppConfig` directly from a dictionary (primarily for tests)."""

    return AppConfig(data, source_path=source_path)


def clear_cached_configs() -> None:
    """Clear cached configuration objects (useful for tests)."""

    _config_cache.clear()
