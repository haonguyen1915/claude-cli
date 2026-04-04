"""Claude CLI — main entry point."""

from __future__ import annotations

import sys

import typer

from claude_cli import __version__

# Known subcommands — anything else gets passed through to claude
_SUBCOMMANDS = {"init", "use", "run", "status", "account", "config", "usage", "history"}

app = typer.Typer(
    name="claude-cli",
    help="CLI tool for managing multiple Claude Code subscription accounts.",
    no_args_is_help=False,
    invoke_without_command=True,
    rich_markup_mode="rich",
    add_completion=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"claude-cli {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Launch Claude Code with the current account, or use a subcommand."""
    try:
        from claude_cli.core.history import record_command
        record_command(sys.argv[1:])
    except Exception:
        pass

    if ctx.invoked_subcommand is not None:
        return

    # No subcommand — quick launch with default account, pass remaining args
    from claude_cli.commands.run import quick_run_command
    ctx.invoke(quick_run_command, args=ctx.args)


def _main() -> None:
    """Entry point that intercepts non-subcommand args before typer."""
    args = sys.argv[1:]

    # If first real arg (after -- or flags) is not a known subcommand,
    # treat everything as passthrough to claude via quick_run
    if args:
        # Strip leading --
        clean = args[1:] if args[0] == "--" else args
        first = clean[0] if clean else None
        if first and first not in _SUBCOMMANDS and first not in ("--help", "-h", "--version", "-V",
                                                                   "--install-completion", "--show-completion"):
            from claude_cli.commands.run import quick_run_command_direct
            quick_run_command_direct(clean)
            return

    app()


# ─── Register sub-command groups ─────────────────────────────────────────────

from claude_cli.commands.account import app as account_app
from claude_cli.commands.config import app as config_app
from claude_cli.commands.history import app as history_app
from claude_cli.commands.usage import app as usage_app

app.add_typer(account_app, name="account", help="Manage account profiles.")
app.add_typer(config_app, name="config", help="Global CLI configuration.")
app.add_typer(usage_app, name="usage", help="View usage information.")
app.add_typer(history_app, name="history", help="Command history.")

# ─── Register top-level commands ─────────────────────────────────────────────

from claude_cli.commands.init import init_command
from claude_cli.commands.run import run_command
from claude_cli.commands.status import status_command
from claude_cli.commands.use import use_command

app.command("init", help="Interactive setup wizard.")(init_command)
app.command("use", help="Switch the active account.")(use_command)
app.command("run", help="Launch Claude Code — select account interactively.")(run_command)
app.command("status", help="Dashboard — all accounts overview.")(status_command)
