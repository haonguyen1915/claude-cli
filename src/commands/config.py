"""claude-cli config — Global CLI configuration."""

from __future__ import annotations

import typer

from claude_cli.core.config import ACCOUNTS_DIR, CONFIG_FILE, SHARED_DIR, load_config
from claude_cli.ui import console, print_detail, print_header

app = typer.Typer(no_args_is_help=True)


@app.command("show")
def show_command() -> None:
    """Show global configuration details."""
    config = load_config()
    print_header("Global Configuration")
    print_detail("Config File", str(CONFIG_FILE))
    print_detail("Shared Dir", str(SHARED_DIR))
    print_detail("Accounts Dir", str(ACCOUNTS_DIR))
    print_detail("Default Account", config.default or "none")
    print_detail("Total Accounts", str(len(config.accounts)))


@app.command("path")
def path_command() -> None:
    """Print the config file path (useful for scripting)."""
    console.print(str(CONFIG_FILE))
