"""Command-line helpers for acquiring WaterlooWorks credentials."""

from __future__ import annotations

import getpass
from typing import Optional, Tuple

from modules.auth import WaterlooWorksAuth
from modules.config import resolve_waterlooworks_credentials


def prompt_for_credentials(
    username: Optional[str] = None, password: Optional[str] = None
) -> Tuple[str, str]:
    """Prompt for credentials, falling back to environment variables."""

    resolved_username, resolved_password = resolve_waterlooworks_credentials(username, password)

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
