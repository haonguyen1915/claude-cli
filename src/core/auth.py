"""OAuth status check and login trigger."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from claude_cli.core.account import get_account_dir


def check_auth_status(name: str) -> str:
    """Check authentication status for an account.

    Returns:
        "valid" — credentials file exists and has token data
        "expired" — credentials file exists but token looks expired
        "none" — no credentials file
    """
    account_dir = get_account_dir(name)
    creds_file = account_dir / ".credentials.json"

    if not creds_file.exists():
        return "none"

    try:
        with open(creds_file) as f:
            data = json.load(f)
        # Check for presence of token fields
        if isinstance(data, dict) and (
            data.get("accessToken") or data.get("oauthTokens")
        ):
            return "valid"
        return "expired"
    except (json.JSONDecodeError, OSError):
        return "expired"


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
