"""claude-cli run — Launch Claude Code with account selection."""

from __future__ import annotations

import os
import shutil
from typing import Optional

import typer

from claude_cli.core.account import get_account_dir, get_default_account, list_accounts
from claude_cli.ui import error, info
from claude_cli.ui.prompts import select_account
from claude_cli.utils.completers import complete_account_name


def _launch(name: str, args: list[str]) -> None:
    """Exec into claude with the given account's config dir."""
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
    os.execvpe(claude_bin, [claude_bin] + args, env)


def quick_run_command_direct(args: list[str]) -> None:
    """Launch Claude Code with default account — called before typer parsing."""
    accounts = list_accounts()
    if not accounts:
        error("No accounts configured. Run 'claude-cli init' first.")
        raise SystemExit(2)

    name = get_default_account()
    if not name:
        error("No default account set. Run 'claude-cli use <name>' or 'claude-cli run'.")
        raise SystemExit(2)

    _launch(name, args)


def quick_run_command(
    args: Optional[list[str]] = typer.Argument(None, help="Arguments passed through to claude"),
) -> None:
    """Launch Claude Code with the current default account (no prompt)."""
    accounts = list_accounts()
    if not accounts:
        error("No accounts configured. Run 'claude-cli init' first.")
        raise typer.Exit(2)

    name = get_default_account()
    if not name:
        error("No default account set. Run 'claude-cli use <name>' or 'claude-cli run'.")
        raise typer.Exit(2)

    _launch(name, list(args) if args else [])


def run_command(
    ctx: typer.Context,
    account: Optional[str] = typer.Option(
        None, "--account", "-a",
        help="Account to use (skip interactive prompt)",
        autocompletion=complete_account_name,
    ),
    args: Optional[list[str]] = typer.Argument(None, help="Arguments passed through to claude"),
) -> None:
    """Launch Claude Code — interactively select account (or use -a to specify)."""
    if ctx.invoked_subcommand is not None:
        return

    accounts = list_accounts()
    if not accounts:
        error("No accounts configured. Run 'claude-cli init' first.")
        raise typer.Exit(2)

    if account:
        name = account
    else:
        name = select_account("Select account:", default=get_default_account())
        if name is None:
            raise typer.Exit(130)

    _launch(name, list(args) if args else [])
