"""claude-cli account — Account management sub-commands."""

from __future__ import annotations

import typer

from claude_cli.core.account import (
    add_account,
    ensure_shared_dir,
    get_account_dir,
    get_default_account,
    list_accounts,
    remove_account,
    rename_account,
    setup_symlinks,
)
from claude_cli.core.auth import check_auth_status, trigger_login
from claude_cli.core.config import SHARED_DIR, load_config
from claude_cli.ui import console, error, info, print_detail, print_header, success
from claude_cli.ui.prompts import confirm, select_account, select_from_list, text_input
from claude_cli.ui.tables import print_accounts_table
from claude_cli.utils.completers import complete_account_name, complete_tier
from claude_cli.utils.formatters import format_date
from claude_cli.utils.validators import validate_account_name, validate_label

app = typer.Typer(no_args_is_help=True)

TIER_CHOICES = ["pro", "max", "team", "enterprise"]


@app.command("list")
def list_command(
    output: str | None = typer.Option(None, "--output", "-O", help="Output format: table, json"),
) -> None:
    """List all configured accounts."""
    config = load_config()
    if not config.accounts:
        info("No accounts configured. Run 'claude-cli init' to get started.")
        raise typer.Exit(0)

    if output == "json":
        import json

        data = {
            name: {
                "label": acc.label,
                "tier": acc.tier,
                "created_at": acc.created_at.isoformat(),
                "is_default": name == config.default,
                "auth_status": check_auth_status(name)[0],
                "expires": check_auth_status(name)[1],
            }
            for name, acc in config.accounts.items()
        }
        console.print_json(json.dumps(data))
        return

    auth_statuses = {name: check_auth_status(name) for name in config.accounts}
    print_accounts_table(config, auth_statuses)


@app.command("add")
def add_command(
    name: str | None = typer.Argument(None, help="Account name slug"),
    label: str | None = typer.Option(None, "--label", "-l", help="Display label"),
    tier: str | None = typer.Option(
        None, "--tier", "-t", help="Subscription tier", autocompletion=complete_tier
    ),
) -> None:
    """Add a new account profile."""
    accounts = list_accounts()

    if not name:
        while True:
            name = text_input("Account name (slug):")
            if name is None:
                raise typer.Exit(130)
            name = name.strip().lower()
            if not validate_account_name(name):
                error("Invalid name. Use lowercase letters, digits, hyphens. Cannot be 'shared'.")
                continue
            if name in accounts:
                error(f"Account '{name}' already exists.")
                continue
            break
    else:
        if not validate_account_name(name):
            error("Invalid account name. Use lowercase letters, digits, hyphens.")
            raise typer.Exit(2)
        if name in accounts:
            error(f"Account '{name}' already exists.")
            raise typer.Exit(2)

    if not label:
        label = text_input("Display label:")
        if label is None:
            raise typer.Exit(130)
        if not validate_label(label):
            error("Label cannot be empty.")
            raise typer.Exit(2)

    if not tier:
        tier = select_from_list("Subscription tier:", TIER_CHOICES)
        if tier is None:
            raise typer.Exit(130)

    if tier not in TIER_CHOICES:
        error(f"Invalid tier '{tier}'. Choose from: {', '.join(TIER_CHOICES)}")
        raise typer.Exit(2)

    add_account(name, label, tier)

    console.print("\n  Opening browser for Claude login...")
    if trigger_login(name):
        success("Authenticated successfully")
    else:
        error("Login failed or claude binary not found on PATH")
        info(f"You can login later with: claude-cli account login {name}")

    success(f'Account "{name}" created')


@app.command("remove")
def remove_command(
    name: str | None = typer.Argument(
        None, help="Account name to remove", autocompletion=complete_account_name
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Remove an account profile (credentials only, shared files untouched)."""
    accounts = list_accounts()
    if not accounts:
        info("No accounts configured.")
        raise typer.Exit(0)

    if not name:
        name = select_account("Select account to remove:")
        if name is None:
            raise typer.Exit(130)

    if name not in accounts:
        error(f"Account '{name}' not found.")
        raise typer.Exit(4)

    if not yes:
        console.print(
            f'\n  [warning]\u26a0 This will remove account "{name}" and its credentials.[/warning]'
        )
        console.print("  Shared settings, rules, and memory are NOT affected.\n")
        proceed = confirm("Continue?", default=False)
        if not proceed:
            info("Cancelled.")
            raise typer.Exit(0)

    remove_account(name)
    success(f'Account "{name}" removed')


@app.command("rename")
def rename_command(
    old_name: str | None = typer.Argument(
        None, help="Current account name", autocompletion=complete_account_name
    ),
    new_name: str | None = typer.Argument(None, help="New account name"),
) -> None:
    """Rename an account slug."""
    accounts = list_accounts()
    if not accounts:
        info("No accounts configured.")
        raise typer.Exit(0)

    if not old_name:
        old_name = select_account("Select account to rename:")
        if old_name is None:
            raise typer.Exit(130)

    if old_name not in accounts:
        error(f"Account '{old_name}' not found.")
        raise typer.Exit(4)

    if not new_name:
        new_name = text_input("New account name (slug):")
        if new_name is None:
            raise typer.Exit(130)
        new_name = new_name.strip().lower()

    if not validate_account_name(new_name):
        error("Invalid new name. Use lowercase letters, digits, hyphens.")
        raise typer.Exit(2)
    if new_name in accounts:
        error(f"Account '{new_name}' already exists.")
        raise typer.Exit(2)

    rename_account(old_name, new_name)
    success(f"Account renamed: {old_name} \u2192 {new_name}")


@app.command("login")
def login_command(
    name: str | None = typer.Argument(
        None, help="Account name (default: active account)", autocompletion=complete_account_name
    ),
) -> None:
    """Re-authenticate (refresh OAuth) for an account."""
    accounts = list_accounts()

    if not name:
        # Try default first, otherwise interactive select
        name = get_default_account()
        if not name:
            if not accounts:
                error("No accounts configured. Run 'claude-cli init' first.")
                raise typer.Exit(2)
            name = select_account("Select account to login:")
            if name is None:
                raise typer.Exit(130)

    if name not in accounts:
        error(f"Account '{name}' not found.")
        raise typer.Exit(4)

    console.print(f"\n  Opening browser for Claude login (account: {name})...")
    if trigger_login(name):
        success("Authenticated successfully")
    else:
        error("Login failed or claude binary not found on PATH")
        raise typer.Exit(3)


@app.command("current")
def current_command() -> None:
    """Show the active account configuration."""
    config = load_config()
    default = config.default

    if not default or default not in config.accounts:
        info("No active account. Run 'claude-cli use <name>' to set one.")
        raise typer.Exit(0)

    account = config.accounts[default]
    auth, expires = check_auth_status(default)
    if auth == "valid":
        status = f"\u2713 logged in (expires {expires})" if expires else "\u2713 logged in"
    elif auth == "expired":
        status = "\u2717 expired"
    else:
        status = "\u2717 none"

    print_header("Current Account")
    print_detail("Name", default)
    print_detail("Label", account.label)
    print_detail("Tier", account.tier)
    print_detail("Status", status)
    print_detail("Config Dir", str(get_account_dir(default)))
    print_detail("Shared Dir", str(SHARED_DIR))
    print_detail("Created", format_date(account.created_at))


@app.command("repair")
def repair_command(
    name: str | None = typer.Argument(
        None, help="Account name (default: all accounts)", autocompletion=complete_account_name
    ),
) -> None:
    """Repair symlinks for account(s) — re-links shared items like commands, skills, etc."""
    accounts = list_accounts()
    if not accounts:
        info("No accounts configured.")
        raise typer.Exit(0)

    ensure_shared_dir()

    targets = [name] if name else accounts
    for acct in targets:
        if acct not in accounts:
            error(f"Account '{acct}' not found.")
            raise typer.Exit(4)
        account_dir = get_account_dir(acct)
        setup_symlinks(account_dir)
        success(f"Repaired symlinks for '{acct}'")
