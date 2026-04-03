"""Rich table builders for accounts, usage, and history."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.table import Table

from claude_cli.ui.console import console

if TYPE_CHECKING:
    from claude_cli.models.config import Config
    from claude_cli.models.usage import UsageInfo


# ─── Accounts ────────────────────────────────────────────────────────────────


def print_accounts_table(config: Config, auth_statuses: dict[str, str]) -> None:
    """Print all accounts with auth status."""
    table = Table(title="Claude CLI Accounts", show_lines=False)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Account", style="bold")
    table.add_column("Label")
    table.add_column("Tier", style="tier")
    table.add_column("Status")

    for i, (name, account) in enumerate(config.accounts.items(), 1):
        is_active = name == config.default
        display_name = f"{name} (active)" if is_active else name
        auth = auth_statuses.get(name, "unknown")
        if auth == "valid":
            status = "[green]\u2713 logged in[/green]"
        elif auth == "expired":
            status = "[red]\u2717 expired[/red]"
        else:
            status = "[dim]\u2717 none[/dim]"

        table.add_row(
            str(i),
            f"[green]{display_name}[/green]" if is_active else display_name,
            account.label,
            account.tier,
            status,
        )

    console.print(table)


# ─── Status ──────────────────────────────────────────────────────────────────


def print_status_table(config: Config, auth_statuses: dict[str, str]) -> None:
    """Print status dashboard table."""
    table = Table(title="Claude CLI Status", show_lines=False)
    table.add_column("Account", style="bold")
    table.add_column("Tier", style="tier")
    table.add_column("Auth")
    table.add_column("Status")

    for name, account in config.accounts.items():
        is_active = name == config.default
        prefix = "\u25cf " if is_active else "  "
        auth = auth_statuses.get(name, "unknown")
        if auth == "valid":
            auth_display = "[green]\u2713 valid[/green]"
            status_display = "Active"
        elif auth == "expired":
            auth_display = "[red]\u2717 expired[/red]"
            status_display = "Needs login"
        else:
            auth_display = "[dim]\u2717 none[/dim]"
            status_display = "Needs login"

        table.add_row(
            f"{prefix}{name}",
            account.tier,
            auth_display,
            status_display,
        )

    console.print(table)


# ─── Usage ───────────────────────────────────────────────────────────────────


def print_usage_summary_table(usage_list: list[UsageInfo]) -> None:
    """Print usage summary for all accounts."""
    table = Table(title="Claude Usage Summary", show_lines=False)
    table.add_column("Account", style="bold")
    table.add_column("Tier", style="tier")
    table.add_column("Billing Period")
    table.add_column("Status")

    for usage in usage_list:
        period = "N/A"
        if usage.period:
            period = f"{usage.period.start.strftime('%b %d')} \u2014 {usage.period.end.strftime('%b %d')}"

        if "active" in usage.status.lower():
            status = f"[green]\u2713 {usage.status}[/green]"
        elif "limit" in usage.status.lower():
            status = f"[yellow]\u26a0 {usage.status}[/yellow]"
        else:
            status = usage.status

        table.add_row(usage.account_name, usage.tier, period, status)

    console.print(table)


# ─── History ─────────────────────────────────────────────────────────────────


def print_history_table(entries: list[dict[str, str]]) -> None:
    """Print command history in linux history style: <id> <cmd>."""
    width = len(str(len(entries)))
    for i, entry in enumerate(entries, 1):
        cmd = entry.get("command", "")
        console.print(f" [dim]{i:>{width}}[/dim]  {cmd}")
