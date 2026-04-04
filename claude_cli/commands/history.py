"""claude-cli history — View command history."""

from __future__ import annotations

from typing import Optional

import typer

from claude_cli.core.history import clear_history, get_history
from claude_cli.ui import info, success
from claude_cli.ui.tables import print_history_table

app = typer.Typer(invoke_without_command=True)


@app.callback(invoke_without_command=True)
def history_command(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of entries to show"),
    clear: bool = typer.Option(False, "--clear", help="Clear all history"),
) -> None:
    """View CLI command history."""
    if clear:
        clear_history()
        success("History cleared.")
        return

    entries = get_history(limit=limit)
    if not entries:
        info("No command history yet.")
        raise typer.Exit(0)

    print_history_table(entries)
