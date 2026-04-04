"""Questionary prompt wrappers for interactive CLI."""

from __future__ import annotations

from typing import Any

import questionary
from questionary import Style

custom_style = Style(
    [
        ("qmark", "fg:cyan bold"),
        ("question", "fg:white bold"),
        ("answer", "fg:green bold"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("selected", "fg:green"),
        ("separator", "fg:white"),
        ("instruction", "fg:white"),
        ("text", "fg:white"),
    ]
)


def select_from_list(
    message: str,
    choices: list[str],
) -> str | None:
    """Single selection from a list."""
    result = questionary.select(
        message,
        choices=choices,
        style=custom_style,
    ).ask()
    return result


def fuzzy_select(
    message: str,
    choices: list[str],
    default: str = "",
) -> str | None:
    """Fuzzy autocomplete selection — type to filter, tab to complete."""
    result = questionary.autocomplete(
        message,
        choices=choices,
        default=default,
        style=custom_style,
        match_middle=True,
    ).ask()
    return result


def text_input(
    message: str,
    default: str = "",
    validate: Any = None,
) -> str | None:
    """Text input with optional validation and default."""
    kwargs: dict[str, Any] = {
        "message": message,
        "default": default,
        "style": custom_style,
    }
    if validate is not None:
        kwargs["validate"] = validate
    result = questionary.text(**kwargs).ask()
    return result


def confirm(message: str, default: bool = True) -> bool | None:
    """Yes/No confirmation."""
    result = questionary.confirm(
        message,
        default=default,
        style=custom_style,
    ).ask()
    return result


def password_input(message: str) -> str | None:
    """Password input (masked)."""
    result = questionary.password(
        message,
        style=custom_style,
    ).ask()
    return result


def select_account(message: str = "Select account:", default: str | None = None) -> str | None:
    """Interactive account selector with labels.

    Shows: name  — label (active)
    Returns the account name slug, or None on cancel.
    """
    from claude_cli.core.config import load_config

    config = load_config()
    if not config.accounts:
        return None

    choices = []
    default_choice = None
    for name, acc in config.accounts.items():
        suffix = " (active)" if name == config.default else ""
        choice = f"{name}  \u2014 {acc.label}{suffix}"
        choices.append(choice)
        if name == default:
            default_choice = choice

    selection = questionary.select(
        message,
        choices=choices,
        default=default_choice,
        style=custom_style,
    ).ask()
    if selection is None:
        return None
    # Extract account name (first token before whitespace)
    return selection.split()[0].strip()
