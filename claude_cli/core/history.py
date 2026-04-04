"""Command history tracking."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from claude_cli.core.config import CONFIG_DIR

HISTORY_FILE = CONFIG_DIR / "history.jsonl"
MAX_HISTORY = 500


def record_command(args: list[str]) -> None:
    """Record a CLI command invocation."""
    if "--help" in args or "-h" in args:
        return
    if args and args[0] == "history":
        return

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    command = "claude-cli " + " ".join(args)
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    entries = _load_entries()
    entries = [e for e in entries if e.get("command") != command]
    entries.append({"command": command, "timestamp": timestamp})

    if len(entries) > MAX_HISTORY:
        entries = entries[-MAX_HISTORY:]

    with open(HISTORY_FILE, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def get_history(limit: int = 50) -> list[dict[str, str]]:
    """Get recent command history (oldest first, newest last)."""
    entries = _load_entries()
    return entries[-limit:]


def clear_history() -> None:
    """Clear all command history."""
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()


def _load_entries() -> list[dict[str, str]]:
    """Load history entries from JSONL file."""
    if not HISTORY_FILE.exists():
        return []
    entries: list[dict[str, str]] = []
    with open(HISTORY_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries
