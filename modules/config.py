"""Configuration helpers for WaterlooWorks automation."""

from __future__ import annotations

import os
from typing import Optional, Tuple

from dotenv import load_dotenv

_env_loaded = False


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
