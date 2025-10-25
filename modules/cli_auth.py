"""Command-line helpers for acquiring WaterlooWorks credentials."""

from __future__ import annotations

import getpass
import os
from typing import Optional, Tuple

from modules.auth import WaterlooWorksAuth


def prompt_for_credentials(
    username: Optional[str] = None, password: Optional[str] = None
) -> Tuple[str, str]:
    """Prompt for credentials, falling back to environment variables."""

    resolved_username = username or os.getenv("WATERLOOWORKS_USERNAME")
    resolved_password = password or os.getenv("WATERLOOWORKS_PASSWORD")

    if not resolved_username:
        resolved_username = input("Username (UW email): ").strip()

    if not resolved_password:
        resolved_password = getpass.getpass("Password: ")

    return resolved_username, resolved_password


def obtain_authenticated_session(
    username: Optional[str] = None, password: Optional[str] = None
) -> WaterlooWorksAuth:
    """Authenticate with WaterlooWorks and return the session wrapper."""

    resolved_username, resolved_password = prompt_for_credentials(username, password)
    auth = WaterlooWorksAuth(resolved_username, resolved_password)
    auth.login()
    return auth
