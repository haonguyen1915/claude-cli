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
    import time
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
