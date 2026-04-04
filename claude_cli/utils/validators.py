"""Input validators for CLI arguments."""

from __future__ import annotations

import re


def validate_account_name(name: str) -> bool:
    """Validate account name slug.

    Rules:
    - Only lowercase letters, digits, hyphens
    - Cannot be 'shared' (reserved directory name)
    - 1-50 chars
    """
    if not name or len(name) > 50:
        return False
    if name == "shared":
        return False
    return bool(re.match(r"^[a-z0-9][a-z0-9-]*$", name))


def validate_label(label: str) -> bool:
    """Validate account display label (non-empty, reasonable length)."""
    if not label or not label.strip():
        return False
    return len(label.strip()) <= 100
