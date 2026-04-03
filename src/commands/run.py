"""claude-cli run — Launch Claude Code with the active account."""

from __future__ import annotations

import os
import shutil
from typing import Optional

import typer

from claude_cli.core.account import get_account_dir, get_default_account, list_accounts
from claude_cli.ui import error, info
from claude_cli.ui.prompts import select_account
from claude_cli.utils.completers import complete_account_name


def run_command(
    account: Optional[str] = typer.Option(
        None, "--account", "-a",
        help="Account to use (temporary, does not switch default)",
        autocompletion=complete_account_name,
    ),
    args: Optional[list[str]] = typer.Argument(None, help="Arguments passed through to claude"),
) -> None:
    """Launch Claude Code with the active (or specified) account."""
    accounts = list_accounts()
    if not accounts:
        error("No accounts configured. Run 'claude-cli init' first.")
        raise typer.Exit(2)

    if account:
        name = account
    else:
        name = select_account("Select account to run:", default=get_default_account())
        if name is None:
            raise typer.Exit(130)

    accounts = list_accounts()
    if name not in accounts:
        error(f"Account '{name}' not found.")
        raise typer.Exit(4)

    claude_bin = shutil.which("claude")
    if not claude_bin:
        error("'claude' binary not found on PATH.")
        info("Install Claude Code first: https://docs.anthropic.com/en/docs/claude-code")
        raise typer.Exit(1)

    account_dir = get_account_dir(name)
    env = os.environ.copy()
    env["CLAUDE_CONFIG_DIR"] = str(account_dir)

    claude_args = list(args) if args else []

    # Replace the current process with claude
    os.execvpe(claude_bin, [claude_bin] + claude_args, env)
