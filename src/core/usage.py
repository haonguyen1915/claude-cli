"""Usage data fetching (stub — no programmatic API available)."""

from __future__ import annotations

import webbrowser

from claude_cli.core.config import load_config
from claude_cli.models.usage import UsageInfo


def get_usage_info(name: str) -> UsageInfo:
    """Get usage info for an account.

    Returns stub data from config metadata since no programmatic
    usage API is available. Wired for future extension.
    """
    config = load_config()
    account = config.accounts.get(name)
    if not account:
        return UsageInfo(
            account_name=name,
            tier="unknown",
            status="Not found",
        )

    return UsageInfo(
        account_name=name,
        tier=account.tier,
        label=account.label,
        period=None,
        status="Active",
    )


def get_all_usage_info() -> list[UsageInfo]:
    """Get usage info for all accounts."""
    config = load_config()
    return [get_usage_info(name) for name in config.accounts]


def open_usage_page() -> None:
    """Open the Claude usage page in the default browser."""
    webbrowser.open("https://claude.ai/settings/usage")
