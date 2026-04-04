"""claude-cli init — Interactive setup wizard."""

from __future__ import annotations

import shutil
from pathlib import Path

import typer

from claude_cli.core.account import (
    add_account,
    ensure_shared_dir,
    migrate_existing_claude_dir,
    set_default_account,
)
from claude_cli.core.auth import trigger_login
from claude_cli.core.config import config_exists
from claude_cli.ui import console, error, info, success
from claude_cli.ui.prompts import confirm, select_from_list, text_input
from claude_cli.utils.validators import validate_account_name, validate_label

TIER_CHOICES = ["pro", "max", "team", "enterprise"]


def init_command() -> None:
    """Interactive setup wizard — create your first (or next) account."""
    is_first_run = not config_exists()

    if is_first_run:
        console.print("\n[bold]Welcome to Claude CLI![/bold]")
        console.print("  Let's set up your first account.\n")
    else:
        console.print("\n[bold]Adding a new Claude account profile...[/bold]\n")

    # Migration offer on first run
    if is_first_run:
        claude_dir = Path.home() / ".claude"
        if claude_dir.exists():
            console.print(f"  Existing Claude config found at [highlight]{claude_dir}[/highlight]\n")
            migrate = confirm("Migrate existing config to claude-cli?", default=True)
            if migrate is None:
                raise typer.Exit(130)
            if migrate:
                creds_path = migrate_existing_claude_dir()
                success("Shared files moved to ~/.claude-cli/shared/")
                success("Backup saved to ~/.claude.bak/")
                console.print()

                # Prompt for account name for existing credentials
                name = _prompt_account_name()
                label = _prompt_label()
                tier = _prompt_tier()

                account_dir = add_account(name, label, tier)

                # Move existing credentials into the account
                if creds_path and creds_path.exists():
                    shutil.move(str(creds_path), str(account_dir / ".credentials.json"))
                    success(f'Account "{name}" created from existing config')
                else:
                    info("No existing credentials found. Logging in...")
                    if not trigger_login(name):
                        error("Login failed or claude binary not found")

                set_default_account(name)
                success("Set as default")

                # Offer to add another
                console.print()
                another = confirm("Add another account now?", default=False)
                if another:
                    _add_new_account()
                return

    # Normal flow: add a new account
    ensure_shared_dir()
    _add_new_account()

    # On first run, auto-set as default
    if is_first_run:
        return

    set_as_default = confirm("Set as default account?", default=True)
    if set_as_default is None:
        raise typer.Exit(130)


def _add_new_account() -> None:
    """Prompt for account details and create it."""
    name = _prompt_account_name()
    label = _prompt_label()
    tier = _prompt_tier()

    add_account(name, label, tier)

    console.print("\n  Opening browser for Claude login...")
    if trigger_login(name):
        success("Authenticated successfully")
    else:
        error("Login failed or claude binary not found on PATH")
        info("You can login later with: claude-cli account login " + name)

    set_default_account(name)
    success(f'Account "{name}" created and set as default')


def _prompt_account_name() -> str:
    """Prompt for a valid account name slug."""
    while True:
        name = text_input("Account name (slug):")
        if name is None:
            raise typer.Exit(130)
        name = name.strip().lower()
        if validate_account_name(name):
            return name
        error("Invalid name. Use lowercase letters, digits, hyphens. Cannot be 'shared'.")


def _prompt_label() -> str:
    """Prompt for an account display label."""
    while True:
        label = text_input("Display label:")
        if label is None:
            raise typer.Exit(130)
        if validate_label(label):
            return label.strip()
        error("Label cannot be empty.")


def _prompt_tier() -> str:
    """Prompt for subscription tier."""
    tier = select_from_list("Subscription tier:", TIER_CHOICES)
    if tier is None:
        raise typer.Exit(130)
    return tier
