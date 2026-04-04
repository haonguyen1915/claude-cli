"""claude-cli usage — View usage information."""

from __future__ import annotations

import typer

from claude_cli.core.account import get_default_account, list_accounts
from claude_cli.core.usage import get_all_usage_info, get_usage_info, open_usage_page
from claude_cli.ui import console, error, info
from claude_cli.ui.prompts import select_account
from claude_cli.ui.tables import print_usage_detail, print_usage_summary_table
from claude_cli.utils.completers import complete_account_name

app = typer.Typer(no_args_is_help=True)


def _fetch_and_display(
    name: str | None,
    all_accounts: bool,
    output: str | None,
) -> None:
    """Fetch and display usage data once."""
    if all_accounts:
        usage_list = get_all_usage_info()
        if not usage_list:
            info("No accounts configured.")
            raise typer.Exit(0)

        if output == "json":
            import json

            data = [u.model_dump(mode="json") for u in usage_list]
            console.print_json(json.dumps(data))
            return

        print_usage_summary_table(usage_list)
        return

    if not name:
        name = get_default_account()
        if not name:
            accounts = list_accounts()
            if not accounts:
                error("No accounts configured.")
                raise typer.Exit(2)
            name = select_account("Select account:")
            if name is None:
                raise typer.Exit(130)

    accounts = list_accounts()
    if name not in accounts:
        error(f"Account '{name}' not found.")
        raise typer.Exit(4)

    usage = get_usage_info(name)

    if output == "json":
        import json

        console.print_json(json.dumps(usage.model_dump(mode="json")))
        return

    print_usage_detail(usage)


@app.command("show")
def show_command(
    name: str | None = typer.Argument(
        None, help="Account name", autocompletion=complete_account_name
    ),
    all_accounts: bool = typer.Option(False, "--all", "-a", help="Show all accounts"),
    output: str | None = typer.Option(None, "--output", "-O", help="Output format: table, json"),
    watch: int | None = typer.Option(None, "--watch", "-w", help="Auto-refresh every N minutes"),
) -> None:
    """Show usage for one or all accounts."""
    if not watch:
        _fetch_and_display(name, all_accounts, output)
        return

    import time
    from datetime import datetime

    from rich.console import Group
    from rich.live import Live
    from rich.text import Text

    from claude_cli.core.auth import refresh_expiring_tokens
    from claude_cli.ui.tables import build_usage_table

    interval = max(1, watch) * 60
    try:
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                # Auto-refresh tokens near expiry
                refreshed = refresh_expiring_tokens()
                refresh_msg = ""
                if refreshed:
                    refresh_msg = f" · refreshed: {', '.join(refreshed)}"

                if all_accounts:
                    usage_list = get_all_usage_info()
                else:
                    resolved = name or get_default_account()
                    usage_list = [get_usage_info(resolved)] if resolved else []

                now = datetime.now().strftime("%H:%M:%S")
                table = build_usage_table(usage_list)
                footer = Text(
                    f"  Updated {now} · every {watch}m · Ctrl+C to stop{refresh_msg}",
                    style="dim",
                )

                live.update(Group(table, footer))
                time.sleep(interval)
    except KeyboardInterrupt:
        console.print("  [dim]Stopped.[/dim]")


@app.command("open")
def open_command(
    name: str | None = typer.Argument(
        None, help="Account name", autocompletion=complete_account_name
    ),
) -> None:
    """Open the Claude usage page in the browser."""
    open_usage_page()
    info("Opened Claude usage page in browser.")
