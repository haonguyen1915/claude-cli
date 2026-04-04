"""claude-cli use — Switch the active account."""

from __future__ import annotations

from typing import Optional

import typer

from claude_cli.core.account import get_default_account, list_accounts, set_default_account
from claude_cli.ui import error, info, success
from claude_cli.ui.prompts import select_account
from claude_cli.utils.completers import complete_account_name


def use_command(
    name: Optional[str] = typer.Argument(
        None, help="Account name to switch to", autocompletion=complete_account_name
    ),
) -> None:
    """Switch the active account (interactive or direct)."""
    accounts = list_accounts()
    if not accounts:
        info("No accounts configured. Run 'claude-cli init' to get started.")
        raise typer.Exit(0)

    if not name:
        name = select_account("Select account:")
        if name is None:
            raise typer.Exit(130)

    if name not in accounts:
        error(f"Account '{name}' not found.")
        raise typer.Exit(4)

    current = get_default_account()
    if name == current:
        info(f"Already using account: {name}")
        return

    set_default_account(name)
    success(f"Switched to account: {name}")
