"""claude-cli status — Dashboard overview of all accounts."""

from __future__ import annotations

import typer

from claude_cli.core.auth import check_auth_status
from claude_cli.core.config import SHARED_DIR, load_config
from claude_cli.ui import console, info
from claude_cli.ui.tables import print_status_table


def status_command() -> None:
    """Quick overview of all accounts — a dashboard view."""
    config = load_config()

    if not config.accounts:
        info("No accounts configured. Run 'claude-cli init' to get started.")
        raise typer.Exit(0)

    auth_statuses = {name: check_auth_status(name) for name in config.accounts}
    print_status_table(config, auth_statuses)

    # Summary line
    active = config.default or "none"
    total = len(config.accounts)
    console.print(f"  Active: [bold]{active}[/bold] | {total} account(s) configured")

    # Shared files check
    shared_items = {
        "settings": SHARED_DIR / "settings.json",
        "rules": SHARED_DIR / "rules",
        "agents": SHARED_DIR / "agents",
        "MCP": SHARED_DIR / ".claude.json",
    }
    checks = []
    for label, path in shared_items.items():
        marker = "\u2713" if path.exists() else "\u2717"
        checks.append(f"{label} {marker}")
    console.print(f"  Shared: {' '.join(checks)}", style="dim")

    console.print()
    console.print('  Run "claude-cli use <name>" to switch.', style="dim")
    console.print('  Run "claude-cli account login <name>" to re-authenticate.', style="dim")
