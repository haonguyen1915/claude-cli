"""claude-cli usage — View usage information."""

from __future__ import annotations

from typing import Optional

import typer

from claude_cli.core.account import get_default_account, list_accounts
from claude_cli.core.config import load_config
from claude_cli.core.usage import get_all_usage_info, get_usage_info, open_usage_page
from claude_cli.ui import console, error, info, print_detail, print_header
from claude_cli.ui.prompts import select_account
from claude_cli.ui.tables import print_usage_summary_table
from claude_cli.utils.completers import complete_account_name

app = typer.Typer(no_args_is_help=True)


@app.command("show")
def show_command(
    name: Optional[str] = typer.Argument(
        None, help="Account name", autocompletion=complete_account_name
    ),
    all_accounts: bool = typer.Option(False, "--all", "-a", help="Show all accounts"),
    output: Optional[str] = typer.Option(None, "--output", "-O", help="Output format: table, json"),
) -> None:
    """Show usage for one or all accounts."""
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
        console.print()
        console.print('  Tip: Run "claude-cli usage show <account>" for details.', style="dim")
        return

    # Single account
    if not name:
        name = get_default_account()
        if not name:
            # No default — interactive select
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

    config = load_config()
    account = config.accounts[name]
    print_header(f"Usage: {name} ({account.label})")
    print_detail("Tier", account.tier.capitalize())
    print_detail("Status", usage.status)
    console.print()
    info("Detailed usage data is not available programmatically.")
    info('Run "claude-cli usage open" to view usage in the browser.')


@app.command("open")
def open_command(
    name: Optional[str] = typer.Argument(
        None, help="Account name", autocompletion=complete_account_name
    ),
) -> None:
    """Open the Claude usage page in the browser."""
    open_usage_page()
    info("Opened Claude usage page in browser.")
