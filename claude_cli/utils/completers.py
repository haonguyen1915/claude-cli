"""Shell auto-completion helpers for Typer arguments and options."""

from __future__ import annotations


def complete_account_name(incomplete: str) -> list[str]:
    """Return account names matching the incomplete prefix (for shell completion)."""
    try:
        from claude_cli.core.account import list_accounts

        return [name for name in list_accounts() if name.startswith(incomplete)]
    except Exception:
        return []


def complete_tier(incomplete: str) -> list[str]:
    """Return tier choices matching the incomplete prefix."""
    tiers = ["pro", "max", "team", "enterprise"]
    return [t for t in tiers if t.startswith(incomplete)]
