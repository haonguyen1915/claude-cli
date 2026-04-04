"""claude-cli usage — View usage information."""

from __future__ import annotations

from typing import Optional

import typer

from claude_cli.core.account import get_default_account, list_accounts
from claude_cli.core.usage import get_all_usage_info, get_usage_info, open_usage_page
from claude_cli.ui import console, error, info
from claude_cli.ui.prompts import select_account
from claude_cli.ui.tables import print_usage_detail, print_usage_summary_table
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
        return

    # Single account
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


@app.command("open")
def open_command(
    name: Optional[str] = typer.Argument(
        None, help="Account name", autocompletion=complete_account_name
    ),
) -> None:
    """Open the Claude usage page in the browser."""
    open_usage_page()
    info("Opened Claude usage page in browser.")
