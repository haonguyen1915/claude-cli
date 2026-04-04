"""Usage data fetching via Anthropic OAuth usage API."""

from __future__ import annotations

import hashlib
import json
import subprocess
import webbrowser
from getpass import getuser
from pathlib import Path

from claude_cli.core.account import get_account_dir
from claude_cli.core.config import load_config
from claude_cli.models.usage import ApiUsageData, ExtraUsage, RateWindow, UsageInfo

USAGE_API_URL = "https://api.anthropic.com/api/oauth/usage"
KEYCHAIN_SERVICE_PREFIX = "Claude Code-credentials"


def _keychain_service_name(account_dir: Path) -> str:
    """Derive the macOS Keychain service name for an account's config dir.

    Claude Code stores credentials in macOS Keychain using:
      service = "Claude Code-credentials-<sha256[:8]>"
    where the hash is computed from the absolute config dir path.
    The default ~/.claude uses "Claude Code-credentials" (no suffix).
    """
    default_claude_dir = Path.home() / ".claude"
    if account_dir.resolve() == default_claude_dir.resolve():
        return KEYCHAIN_SERVICE_PREFIX
    suffix = hashlib.sha256(str(account_dir).encode()).hexdigest()[:8]
    return f"{KEYCHAIN_SERVICE_PREFIX}-{suffix}"


def _get_oauth_token(account_name: str) -> str | None:
    """Extract the OAuth access token from macOS Keychain for an account."""
    account_dir = get_account_dir(account_name)
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
        data = json.loads(result.stdout.strip())
        return data.get("claudeAiOauth", {}).get("accessToken")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return None


def _fetch_usage_api(token: str) -> tuple[ApiUsageData | None, str]:
    """Call the Anthropic OAuth usage API. Returns (data, status_message)."""
    try:
        result = subprocess.run(
            [
                "curl", "-s", "--max-time", "5",
                USAGE_API_URL,
                "-H", f"Authorization: Bearer {token}",
                "-H", "anthropic-beta: oauth-2025-04-20",
                "-H", "Content-Type: application/json",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None, "API request failed"

        data = json.loads(result.stdout)

        if "error" in data:
            err_type = data["error"].get("type", "unknown")
            if "rate_limit" in err_type:
                return None, "Rate limited — try again later"
            return None, f"API error: {err_type}"

        def parse_window(raw: dict | None) -> RateWindow | None:
            if not raw or "utilization" not in raw:
                return None
            return RateWindow(utilization=raw["utilization"], resets_at=raw["resets_at"])

        extra_raw = data.get("extra_usage")
        extra = None
        if extra_raw and isinstance(extra_raw, dict):
            extra = ExtraUsage(**extra_raw)

        return ApiUsageData(
            five_hour=parse_window(data.get("five_hour")),
            seven_day=parse_window(data.get("seven_day")),
            seven_day_opus=parse_window(data.get("seven_day_opus")),
            seven_day_sonnet=parse_window(data.get("seven_day_sonnet")),
            extra_usage=extra,
        ), "Active"
    except subprocess.TimeoutExpired:
        return None, "API timeout"
    except (json.JSONDecodeError, OSError):
        return None, "API unavailable"


# Cache last successful API usage per account
_usage_cache: dict[str, "ApiUsageData"] = {}


def get_usage_info(name: str) -> UsageInfo:
    """Get usage info for an account, including live API data.

    On rate limit or error, returns cached data with error status.
    """
    config = load_config()
    account = config.accounts.get(name)
    if not account:
        return UsageInfo(account_name=name, tier="unknown", status="Not found")

    token = _get_oauth_token(name)
    api_usage = None
    status = "Active"

    if token:
        api_usage, status = _fetch_usage_api(token)
        if api_usage:
            _usage_cache[name] = api_usage
            status = "OK"
        elif name in _usage_cache:
            # Use cached data on error
            api_usage = _usage_cache[name]
            status = f"{status} (cached)"
    else:
        status = "No credentials"

    return UsageInfo(
        account_name=name,
        tier=account.tier,
        label=account.label,
        status=status,
        api_usage=api_usage,
    )


_first_fetch_done = False


def get_all_usage_info(delay: float = 20.0) -> list[UsageInfo]:
    """Get usage info for all accounts. First call is parallel, subsequent calls have delay."""
    global _first_fetch_done
    import time

    config = load_config()
    names = list(config.accounts.keys())

    if not _first_fetch_done:
        _first_fetch_done = True
        return [get_usage_info(name) for name in names]

    results = []
    for i, name in enumerate(names):
        results.append(get_usage_info(name))
        if i < len(names) - 1:
            time.sleep(delay)
    return results


def open_usage_page() -> None:
    """Open the Claude usage page in the default browser."""
    webbrowser.open("https://claude.ai/settings/usage")
