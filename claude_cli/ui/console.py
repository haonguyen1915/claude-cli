"""Rich console setup and helper functions."""

from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

custom_theme = Theme(
    {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red bold",
        "highlight": "cyan bold",
        "dim": "dim",
        "account": "bold green",
        "tier": "bold blue",
        "active": "bold cyan",
    }
)

console = Console(theme=custom_theme)


def success(message: str) -> None:
    console.print(f"\u2713 {message}", style="success")


def error(message: str) -> None:
    console.print(f"\u2717 {message}", style="error")


def warning(message: str) -> None:
    console.print(f"\u26a0 {message}", style="warning")


def info(message: str) -> None:
    console.print(f"\u2139 {message}", style="info")


def print_header(text: str) -> None:
    console.print(f"\n[bold]{text}[/bold]")


def print_detail(label: str, value: str) -> None:
    console.print(f"  {label}: [highlight]{value}[/highlight]")
