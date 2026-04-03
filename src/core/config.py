"""Configuration management for ~/.claude-cli/ directory."""

from __future__ import annotations

from pathlib import Path

import yaml

from claude_cli.models.config import Config

CONFIG_DIR = Path.home() / ".claude-cli"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
SHARED_DIR = CONFIG_DIR / "shared"
ACCOUNTS_DIR = CONFIG_DIR / "accounts"


def ensure_config_dir() -> None:
    """Create config directory structure if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SHARED_DIR.mkdir(parents=True, exist_ok=True)
    ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> Config:
    """Load config from YAML file."""
    if not CONFIG_FILE.exists():
        return Config()
    with open(CONFIG_FILE) as f:
        data = yaml.safe_load(f) or {}
    return Config.model_validate(data)


def save_config(config: Config) -> None:
    """Save config to YAML file."""
    ensure_config_dir()
    data = config.model_dump(exclude_none=True, mode="json")
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def config_exists() -> bool:
    """Check if config file exists."""
    return CONFIG_FILE.exists()
