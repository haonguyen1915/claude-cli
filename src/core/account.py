"""Account CRUD and symlink management."""

from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from claude_cli.core.config import ACCOUNTS_DIR, SHARED_DIR, ensure_config_dir, load_config, save_config
from claude_cli.models.config import AccountConfig

# Items symlinked from shared/ into each account directory.
# Only .credentials.json stays per-account (real file).
SYMLINKED_ITEMS = [
    "settings.json",
    ".claude.json",
    "CLAUDE.md",
    "rules",
    "agents",
    "plans",
    "projects",
    "commands",
    "skills",
]

# Subdirectories that must exist in shared/
SHARED_SUBDIRS = [
    "rules",
    "agents",
    "plans",
    "projects",
    "commands",
    "skills",
]

# Placeholder files created in shared/ if they don't exist.
# JSON files need valid JSON content; Claude Code rejects empty files as corrupted.
SHARED_PLACEHOLDER_FILES: dict[str, str] = {
    "settings.json": "{}",
    ".claude.json": "{}",
    "CLAUDE.md": "",
}


def ensure_shared_dir() -> None:
    """Create shared/ with subdirectories and placeholder files.

    If ~/.claude/ has commands/ or skills/, copy them into shared/ as seed data.
    """
    ensure_config_dir()
    for subdir in SHARED_SUBDIRS:
        (SHARED_DIR / subdir).mkdir(parents=True, exist_ok=True)
    for fname, default_content in SHARED_PLACEHOLDER_FILES.items():
        fpath = SHARED_DIR / fname
        if not fpath.exists():
            fpath.write_text(default_content)
    _seed_from_claude_dir()


# Directories to seed from ~/.claude/ into shared/ on first setup.
_SEED_DIRS = ["commands", "skills"]


def _seed_from_claude_dir() -> None:
    """Copy commands/ and skills/ from ~/.claude/ into shared/ if shared copies are empty."""
    claude_dir = Path.home() / ".claude"
    for dirname in _SEED_DIRS:
        src = claude_dir / dirname
        dst = SHARED_DIR / dirname
        if not src.is_dir():
            continue
        # Only seed if the shared dir is empty (don't overwrite user customizations)
        existing = list(dst.iterdir()) if dst.exists() else []
        if existing:
            continue
        for item in src.iterdir():
            if item.name.startswith(".") or item.name == "__pycache__":
                continue
            dest_item = dst / item.name
            if item.is_dir():
                shutil.copytree(item, dest_item)
            else:
                shutil.copy2(item, dest_item)


def setup_symlinks(account_dir: Path) -> None:
    """Create relative symlinks from account dir to shared/ items.

    Uses relative paths (../../shared/<item>) for portability.
    """
    for item in SYMLINKED_ITEMS:
        link_path = account_dir / item
        # Relative path from account dir to shared item
        target = os.path.relpath(SHARED_DIR / item, account_dir)
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink() if link_path.is_file() or link_path.is_symlink() else shutil.rmtree(link_path)
        link_path.symlink_to(target)


def add_account(name: str, label: str, tier: str) -> Path:
    """Create a new account directory with symlinks and update config.

    Returns the account directory path.
    """
    ensure_shared_dir()
    account_dir = ACCOUNTS_DIR / name
    account_dir.mkdir(parents=True, exist_ok=True)
    setup_symlinks(account_dir)

    config = load_config()
    config.accounts[name] = AccountConfig(
        label=label,
        tier=tier,  # type: ignore[arg-type]
        created_at=datetime.now(tz=timezone.utc),
    )
    save_config(config)
    return account_dir


def remove_account(name: str) -> None:
    """Remove an account directory and update config."""
    account_dir = ACCOUNTS_DIR / name
    if account_dir.exists():
        shutil.rmtree(account_dir)

    config = load_config()
    config.accounts.pop(name, None)
    if config.default == name:
        config.default = None
    save_config(config)


def rename_account(old_name: str, new_name: str) -> None:
    """Rename an account directory and update config."""
    old_dir = ACCOUNTS_DIR / old_name
    new_dir = ACCOUNTS_DIR / new_name
    if old_dir.exists():
        old_dir.rename(new_dir)
        # Re-create symlinks since relative paths stay the same depth
        setup_symlinks(new_dir)

    config = load_config()
    if old_name in config.accounts:
        config.accounts[new_name] = config.accounts.pop(old_name)
    if config.default == old_name:
        config.default = new_name
    save_config(config)


def get_account_dir(name: str) -> Path:
    """Get the filesystem path for an account's config directory."""
    return ACCOUNTS_DIR / name


def list_accounts() -> list[str]:
    """List all account names from config."""
    config = load_config()
    return list(config.accounts.keys())


def get_default_account() -> str | None:
    """Get the default account name."""
    config = load_config()
    return config.default


def set_default_account(name: str) -> None:
    """Set the default active account."""
    config = load_config()
    if name not in config.accounts:
        raise ValueError(f"Account '{name}' not found")
    config.default = name
    save_config(config)


def migrate_existing_claude_dir() -> Path | None:
    """Migrate existing ~/.claude/ to claude-cli structure.

    1. Back up ~/.claude/ to ~/.claude.bak/
    2. Move shared items to ~/.claude-cli/shared/
    3. Return credentials path if found, else None.
    """
    claude_dir = Path.home() / ".claude"
    backup_dir = Path.home() / ".claude.bak"

    if not claude_dir.exists():
        return None

    ensure_shared_dir()

    # Back up the entire directory
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    shutil.copytree(claude_dir, backup_dir, symlinks=True)

    # Move shared items
    credentials_path = None
    for item in SYMLINKED_ITEMS:
        src = claude_dir / item
        dst = SHARED_DIR / item
        if src.exists():
            if dst.exists():
                if dst.is_dir():
                    shutil.rmtree(dst)
                else:
                    dst.unlink()
            shutil.move(str(src), str(dst))

    # Check for credentials
    creds = claude_dir / ".credentials.json"
    if creds.exists():
        credentials_path = creds

    return credentials_path
