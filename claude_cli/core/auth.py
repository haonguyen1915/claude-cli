"""OAuth status check and login trigger."""

from __future__ import annotations

import shutil
import subprocess
from getpass import getuser

from claude_cli.core.account import get_account_dir
from claude_cli.core.usage import _keychain_service_name


def check_auth_status(name: str) -> tuple[str, str]:
    """Check authentication status for an account via macOS Keychain.

    Returns:
        (status, expires_display) where status is "valid", "expired", or "none"
        and expires_display is a human-readable expiry string.
    """
    import json
    from datetime import datetime, timezone

    account_dir = get_account_dir(name)
    service = _keychain_service_name(account_dir)
    username = getuser()

    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", username, "-w"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return "none", ""

        data = json.loads(result.stdout.strip())
        oauth = data.get("claudeAiOauth", {})
        expires_at_ms = oauth.get("expiresAt")

        if expires_at_ms is None:
            return "valid", ""

        expires_dt = datetime.fromtimestamp(expires_at_ms / 1000, tz=timezone.utc).astimezone()
        now = datetime.now(tz=timezone.utc)
        diff = expires_dt - now
        total_sec = diff.total_seconds()

        if total_sec < 0:
            return "expired", expires_dt.strftime("%H:%M")

        hours = int(total_sec // 3600)
        mins = int((total_sec % 3600) // 60)
        if hours > 0:
            expires_display = f"in {hours}h {mins}m"
        else:
            expires_display = f"in {mins}m"

        return "valid", expires_display
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return "none", ""


OAUTH_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
OAUTH_TOKEN_URL = "https://console.anthropic.com/v1/oauth/token"

# Refresh when token expires within this many minutes
REFRESH_THRESHOLD_MINUTES = 120


def _get_keychain_data(name: str) -> dict | None:
    """Read raw keychain JSON for an account."""
    import json

    account_dir = get_account_dir(name)
    service = _keychain_service_name(account_dir)
    username = getuser()

    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", username, "-w"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout.strip())
    except (subprocess.TimeoutExpired, Exception):
        return None


def _save_keychain_data(name: str, data: dict) -> bool:
    """Write updated keychain JSON for an account."""
    import json

    account_dir = get_account_dir(name)
    service = _keychain_service_name(account_dir)
    username = getuser()
    payload = json.dumps(data)

    # Delete old entry, then add new
    subprocess.run(
        ["security", "delete-generic-password", "-s", service, "-a", username],
        capture_output=True,
        timeout=5,
    )
    result = subprocess.run(
        ["security", "add-generic-password", "-s", service, "-a", username, "-w", payload],
        capture_output=True,
        timeout=5,
    )
    return result.returncode == 0


def token_needs_refresh(name: str) -> bool:
    """Check if token expires within REFRESH_THRESHOLD_MINUTES."""
    import time

    data = _get_keychain_data(name)
    if not data:
        return False
    oauth = data.get("claudeAiOauth", {})
    expires_at_ms = oauth.get("expiresAt")
    if expires_at_ms is None:
        return False

    remaining_sec = (expires_at_ms / 1000) - time.time()
    return remaining_sec < REFRESH_THRESHOLD_MINUTES * 60


def refresh_token(name: str) -> bool:
    """Refresh OAuth token using the refresh_token grant. Returns True on success."""
    import json

    data = _get_keychain_data(name)
    if not data:
        return False

    oauth = data.get("claudeAiOauth", {})
    refresh_tok = oauth.get("refreshToken")
    if not refresh_tok:
        return False

    try:
        result = subprocess.run(
            [
                "curl", "-s", "--max-time", "10",
                "-X", "POST", OAUTH_TOKEN_URL,
                "-H", "Content-Type: application/json",
                "-d", json.dumps({
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_tok,
                    "client_id": OAUTH_CLIENT_ID,
                }),
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return False

        resp = json.loads(result.stdout)
        if "access_token" not in resp:
            return False

        # Update keychain with new tokens
        import time
        expires_in = resp.get("expires_in", 28800)  # default 8h
        oauth["accessToken"] = resp["access_token"]
        if "refresh_token" in resp:
            oauth["refreshToken"] = resp["refresh_token"]
        oauth["expiresAt"] = int((time.time() + expires_in) * 1000)
        data["claudeAiOauth"] = oauth

        return _save_keychain_data(name, data)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return False


def refresh_expiring_tokens() -> list[str]:
    """Refresh tokens for all accounts that are near expiry. Returns list of refreshed account names."""
    from claude_cli.core.account import list_accounts

    refreshed = []
    for name in list_accounts():
        if token_needs_refresh(name):
            if refresh_token(name):
                refreshed.append(name)
    return refreshed


def trigger_login(name: str) -> bool:
    """Run `claude --login` with CLAUDE_CONFIG_DIR set to the account directory.

    Returns True if the login process completed (exit code 0).
    """
    account_dir = get_account_dir(name)
    claude_bin = _find_claude_binary()
    if not claude_bin:
        return False

    import os

    env = os.environ.copy()
    env["CLAUDE_CONFIG_DIR"] = str(account_dir)

    result = subprocess.run(
        [claude_bin, "login"],
        env=env,
    )
    return result.returncode == 0


def _find_claude_binary() -> str | None:
    """Find the claude binary on PATH."""
    return shutil.which("claude")
