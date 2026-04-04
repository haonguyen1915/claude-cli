"""Rich table builders for accounts, usage, and history."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from rich.table import Table

from claude_cli.ui.console import console

if TYPE_CHECKING:
    from claude_cli.models.config import Config
    from claude_cli.models.usage import RateWindow, UsageInfo


# ─── Accounts ────────────────────────────────────────────────────────────────


def print_accounts_table(config: Config, auth_statuses: dict[str, tuple[str, str]]) -> None:
    """Print all accounts with auth status and token expiry."""
    table = Table(title="Claude CLI Accounts", show_lines=False)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Account", style="bold")
    table.add_column("Label")
    table.add_column("Tier", style="tier")
    table.add_column("Status")
    table.add_column("Expires", style="dim")

    for i, (name, account) in enumerate(config.accounts.items(), 1):
        is_active = name == config.default
        display_name = f"{name} (active)" if is_active else name
        auth, expires = auth_statuses.get(name, ("unknown", ""))
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
            expires,
        )

    console.print(table)


# ─── Status ──────────────────────────────────────────────────────────────────


def print_status_table(config: Config, auth_statuses: dict[str, tuple[str, str]]) -> None:
    """Print status dashboard table."""
    table = Table(title="Claude CLI Status", show_lines=False)
    table.add_column("Account", style="bold")
    table.add_column("Tier", style="tier")
    table.add_column("Auth")
    table.add_column("Expires", style="dim")

    for name, account in config.accounts.items():
        is_active = name == config.default
        prefix = "\u25cf " if is_active else "  "
        auth, expires = auth_statuses.get(name, ("unknown", ""))
        if auth == "valid":
            auth_display = "[green]\u2713 valid[/green]"
        elif auth == "expired":
            auth_display = "[red]\u2717 expired[/red]"
        else:
            auth_display = "[dim]\u2717 none[/dim]"

        table.add_row(
            f"{prefix}{name}",
            account.tier,
            auth_display,
            expires,
        )

    console.print(table)


# ─── Usage ───────────────────────────────────────────────────────────────────


def _progress_bar(pct: float, width: int = 20) -> str:
    """Render a text-based progress bar with color (no trailing %)."""
    filled = int(width * pct / 100)
    empty = width - filled
    if pct >= 80:
        color = "red"
    elif pct >= 50:
        color = "yellow"
    else:
        color = "cyan"
    filled_str = "\u2588" * filled
    empty_str = "\u2591" * empty
    return f"[{color}]{filled_str}[/{color}][dim]{empty_str}[/dim]"


def _format_reset_time(resets_at: datetime) -> str:
    """Format reset time as human-friendly string."""
    now = datetime.now(timezone.utc)
    if resets_at.tzinfo is None:
        resets_at = resets_at.replace(tzinfo=timezone.utc)

    delta = resets_at - now
    total_hours = delta.total_seconds() / 3600

    if total_hours <= 0:
        return "now"
    elif total_hours < 1:
        mins = int(delta.total_seconds() / 60)
        return f"in {mins}m"
    elif total_hours < 24:
        return f"in {total_hours:.0f}h"
    else:
        local = resets_at.astimezone()
        return local.strftime("%b %d %I%p")


def _status_style(status: str) -> str:
    """Return styled status string."""
    s = status.lower()
    if s == "ok":
        return "[green]OK[/green]"
    elif "cached" in s:
        return f"[yellow]{status}[/yellow]"
    elif "rate limit" in s or "error" in s or "timeout" in s:
        return f"[red]{status}[/red]"
    elif "no credentials" in s:
        return f"[dim]{status}[/dim]"
    return f"[dim]{status}[/dim]"


# Row: (account, tier, metric, bar, resets, status)
_Row = tuple[str, str, str, str, str, str]


def _collect_rows(usage: UsageInfo) -> list[_Row]:
    """Collect table rows for one account."""
    api = usage.api_usage
    rows: list[_Row] = []

    account_label = usage.account_name
    tier = usage.tier
    styled_status = _status_style(usage.status)

    if not api:
        rows.append((account_label, tier, "", "", "", styled_status))
        return rows

    windows: list[tuple[str, str, RateWindow | None]] = [
        ("Session", "S", api.five_hour),
        ("Week/All", "W", api.seven_day),
        ("Week/Opus", "Op", api.seven_day_opus),
        ("Week/Sonnet", "So", api.seven_day_sonnet),
    ]

    first = True
    for label, _short, window in windows:
        if window is None:
            continue
        pct_str = f"{window.utilization:>3.0f}%"
        rows.append((
            account_label if first else "",
            tier if first else "",
            f"{pct_str} {label}",
            _progress_bar(window.utilization, width=20),
            _format_reset_time(window.resets_at) if window.resets_at else "",
            styled_status if first else "",
        ))
        first = False

    if api.extra_usage and api.extra_usage.is_enabled:
        pct = api.extra_usage.utilization or 0
        pct_str = f"{pct:>3.0f}%"
        rows.append((
            account_label if first else "",
            tier if first else "",
            f"{pct_str} Extra",
            _progress_bar(pct, width=20),
            "",
            styled_status if first else "",
        ))

    return rows


def build_usage_table(usage_list: list[UsageInfo]) -> Table:
    """Build usage table and return the Table object."""
    table = Table(title="Claude Usage Overview", show_lines=False, title_style="bold")
    table.add_column("Account", style="bold")
    table.add_column("Tier", style="cyan", justify="center")
    table.add_column("Metric", no_wrap=True)
    table.add_column("Bar", no_wrap=True)
    table.add_column("Resets", style="dim")
    table.add_column("Status", no_wrap=True)

    for i, usage in enumerate(usage_list):
        rows = _collect_rows(usage)
        for account, tier, metric, bar, resets, status in rows:
            table.add_row(account, tier, metric, bar, resets, status)
        if i < len(usage_list) - 1:
            table.add_section()

    return table


def print_usage_summary_table(usage_list: list[UsageInfo]) -> None:
    """Print usage summary for all accounts as a single table."""
    console.print()
    console.print(build_usage_table(usage_list))
    console.print()


# ─── Usage detail for single account ────────────────────────────────────────


def print_usage_detail(usage: UsageInfo) -> None:
    """Print detailed usage for a single account."""
    print_usage_summary_table([usage])


# ─── History ─────────────────────────────────────────────────────────────────


def print_history_table(entries: list[dict[str, str]]) -> None:
    """Print command history in linux history style: <id> <cmd>."""
    width = len(str(len(entries)))
    for i, entry in enumerate(entries, 1):
        cmd = entry.get("command", "")
        console.print(f" [dim]{i:>{width}}[/dim]  {cmd}")
