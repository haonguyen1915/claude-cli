# CLI Design — claude-cli

## Overview

`claude-cli` is a Python CLI tool for managing multiple Claude Code subscription accounts, built with **Typer + Rich + Pydantic + PyYAML**. Follows the same architecture as [kafka-cli](../README.md).

The tool wraps Claude Code's `CLAUDE_CONFIG_DIR` mechanism to isolate **only OAuth credentials** per account, while sharing all other configuration (settings, MCP servers, rules, agents, memory) via symlinks.

## Core Concept

Claude Code stores all user-level data in a config directory (`~/.claude/` by default). By creating multiple config directories — each with its **own credentials** but **symlinked shared files** — the tool enables:

- One-command account switching (only credentials change)
- Parallel sessions with different accounts
- Shared settings, MCP servers, rules, agents, memory across all accounts
- Usage tracking across all accounts
- Named accounts with metadata

### Architecture: Symlink-Based Isolation

```
~/.claude-cli/
├── config.yaml                         # Account registry (metadata only)
├── history.jsonl                       # CLI command history
│
├── shared/                             # Shared files (the REAL files)
│   ├── settings.json                   # Permissions, hooks, default model
│   ├── .claude.json                    # MCP servers, theme, vim mode
│   ├── CLAUDE.md                       # Personal instructions
│   ├── rules/                          # User-level rules
│   ├── agents/                         # User subagents
│   ├── plans/                          # Implementation plans
│   └── projects/                       # Auto memory per project
│
└── accounts/                           # Per-account directories
    ├── work/                           # CLAUDE_CONFIG_DIR for "work"
    │   ├── .credentials.json           ← REAL FILE (OAuth token, unique)
    │   ├── settings.json               → symlink → ../../shared/settings.json
    │   ├── .claude.json                → symlink → ../../shared/.claude.json
    │   ├── CLAUDE.md                   → symlink → ../../shared/CLAUDE.md
    │   ├── rules/                      → symlink → ../../shared/rules/
    │   ├── agents/                     → symlink → ../../shared/agents/
    │   ├── plans/                      → symlink → ../../shared/plans/
    │   └── projects/                   → symlink → ../../shared/projects/
    │
    ├── personal/                       # CLAUDE_CONFIG_DIR for "personal"
    │   ├── .credentials.json           ← REAL FILE (different OAuth token)
    │   ├── settings.json               → symlink → same shared/
    │   └── ...                         → symlinks
    │
    └── client-a/
        ├── .credentials.json           ← REAL FILE
        └── ...                         → symlinks
```

### What is shared vs isolated

| Data | Shared? | Mechanism |
|------|---------|-----------|
| **OAuth credentials** | Per-account | Real file in each account dir |
| **Settings** (permissions, hooks, model) | Shared | Symlink → `shared/settings.json` |
| **MCP servers** (user scope) | Shared | Symlink → `shared/.claude.json` |
| **CLAUDE.md** (personal instructions) | Shared | Symlink → `shared/CLAUDE.md` |
| **Rules** (user-level) | Shared | Symlink → `shared/rules/` |
| **Agents** (user subagents) | Shared | Symlink → `shared/agents/` |
| **Plans** | Shared | Symlink → `shared/plans/` |
| **Auto memory** (per project) | Shared | Symlink → `shared/projects/` |
| **Theme, vim mode** | Shared | Symlink → `shared/.claude.json` |
| **Project-level files** (`.claude/`, `.mcp.json`, `CLAUDE.md` in repo) | Unaffected | Lives in project repo, not in config dir |

Editing settings from **any account** applies to **all accounts** instantly — they all point to the same file.

### First-Time Migration

If the user already has an existing `~/.claude/` directory, `claude-cli init` will:
1. Move shared files from `~/.claude/` to `~/.claude-cli/shared/`
2. Move credentials to the first account directory
3. Create symlinks in the account directory
4. Original `~/.claude/` is backed up to `~/.claude.bak/`

---

## CLI Command Reference

### Entry Point

```
claude-cli <command> [options]
```

Package name: `claude-util`
Binary name: `claude-cli`

---

### `claude-cli init`

Interactive setup wizard. Creates the first account or adds a new one.

```bash
claude-cli init
```

**First run** prompts:
1. Account name (slug, e.g. `work`, `personal`, `client-a`)
2. Account label (display name, e.g. "Work — Pro", "Personal — Max")
3. Subscription tier: `pro` | `max` | `team` | `enterprise`
4. Migrate existing `~/.claude/` config? (if exists)
5. Opens browser for Claude OAuth login
6. Set as default account? (yes/no)

**Subsequent runs**: add a new account.

```
$ claude-cli init

  Creating new Claude account profile...

  Account name (slug): client-a
  Display label: Client A — Max
  Subscription tier: max

  Opening browser for Claude login...
  ✓ Authenticated successfully

  Set as default account? [Y/n]: y
  ✓ Account "client-a" created and set as default
```

**First run with existing config:**

```
$ claude-cli init

  Existing Claude config found at ~/.claude/

  ? Migrate existing config to claude-cli? [Y/n]: y
    ✓ Shared files moved to ~/.claude-cli/shared/
    ✓ Backup saved to ~/.claude.bak/

  Account name for existing credentials: work
  Display label: Work — Pro
  Subscription tier: pro

  ✓ Account "work" created from existing config
  ✓ Set as default

  ? Add another account now? [y/N]: y
  ...
```

---

### `claude-cli account`

Manage account profiles.

#### `claude-cli account list`

List all configured accounts.

```bash
claude-cli account list
claude-cli account list --output json
```

```
                    Claude CLI Accounts
┏━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━┓
┃ #  ┃ Account      ┃ Label                   ┃ Tier ┃ Status     ┃
┡━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━┩
│ 1  │ work (active)│ Work — Pro              │ pro  │ ✓ logged in│
│ 2  │ personal     │ Personal — Max          │ max  │ ✓ logged in│
│ 3  │ client-a     │ Client A — Max          │ max  │ ✗ expired  │
└────┴──────────────┴─────────────────────────┴──────┴────────────┘
```

#### `claude-cli account add`

Add a new account (non-interactive alternative to `init`).

```bash
# Interactive
claude-cli account add

# Non-interactive
claude-cli account add work --label "Work — Pro" --tier pro
```

Under the hood:
1. Creates `~/.claude-cli/accounts/<name>/`
2. Creates symlinks to `shared/` for all shared files
3. Opens browser for OAuth login → credentials saved to account dir

#### `claude-cli account remove`

Remove an account profile. Only deletes the account directory (credentials + symlinks). Shared files are untouched.

```bash
claude-cli account remove client-a
claude-cli account remove client-a --yes    # Skip confirmation
```

```
⚠ This will remove account "client-a" and its credentials.
  Shared settings, rules, and memory are NOT affected.

  Continue? [y/N]: y
  ✓ Account "client-a" removed
```

#### `claude-cli account rename`

Rename an account slug.

```bash
claude-cli account rename client-a freelance
```

```
✓ Account renamed: client-a → freelance
```

#### `claude-cli account login`

Re-authenticate (refresh OAuth) for an account.

```bash
claude-cli account login              # Current active account
claude-cli account login personal     # Specific account
```

```
  Opening browser for Claude login (account: personal)...
  ✓ Authenticated successfully
```

#### `claude-cli account current`

Show the active account configuration.

```bash
claude-cli account current
```

```
Current Account
  Name:          work
  Label:         Work — Pro
  Tier:          pro
  Status:        ✓ logged in
  Config Dir:    ~/.claude-cli/accounts/work/
  Shared Dir:    ~/.claude-cli/shared/
  Created:       2025-03-15
```

---

### `claude-cli use`

Switch the active account. Top-level command for convenience.

```bash
# Interactive — fuzzy select from all accounts
claude-cli use

# Direct
claude-cli use personal
```

```
$ claude-cli use

  ? Select account:
  ❯ work          — Work — Pro          (active)
    personal      — Personal — Max
    client-a      — Client A — Max

  ✓ Switched to account: personal
```

After switching, all subsequent `claude-cli run` commands use this account.

---

### `claude-cli run`

Launch Claude Code with the active (or specified) account.

```bash
# Run with active account
claude-cli run

# Run with specific account (temporary, does not switch default)
claude-cli run --account personal
claude-cli run -a personal

# Pass-through all arguments to claude
claude-cli run -- --model opus "fix the bug in main.py"
claude-cli run -a work -- -p "review this PR"
```

Under the hood:
```bash
CLAUDE_CONFIG_DIR=~/.claude-cli/accounts/<account>/ claude [args...]
```

Since all shared files are symlinked, Claude Code sees the same settings, MCP servers, rules, agents, and memory — only the OAuth credentials differ.

---

### `claude-cli usage`

View usage information for accounts.

#### `claude-cli usage show`

Show usage for one or all accounts.

```bash
# Current active account
claude-cli usage show

# Specific account
claude-cli usage show work

# All accounts
claude-cli usage show --all

# JSON output
claude-cli usage show --all --output json
```

```
$ claude-cli usage show --all

                    Claude Usage Summary
┏━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Account      ┃ Tier ┃ Billing Period     ┃ Status         ┃
┡━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ work         │ pro  │ Mar 15 — Apr 15    │ ✓ Active       │
│ personal     │ max  │ Mar 01 — Apr 01    │ ✓ Active       │
│ client-a     │ max  │ Mar 20 — Apr 20    │ ⚠ Rate limited │
└──────────────┴──────┴────────────────────┴────────────────┘

  Tip: Run "claude-cli usage show <account>" for detailed breakdown.
```

Detailed view for a single account:

```
$ claude-cli usage show work

Usage: work (Work — Pro)
  Tier:            Pro
  Billing Period:  Mar 15 — Apr 15
  Status:          ✓ Active

  Opus Requests:       145 / 200
  Sonnet Requests:     1,230 (unlimited)
  Haiku Requests:      3,450 (unlimited)

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 72.5% Opus used
```

> **Note**: Usage data availability depends on what Claude Code / Claude.ai exposes. The CLI will attempt to fetch usage via the authenticated session. If usage data is not available programmatically, the tool will open the usage page in the browser as a fallback.

#### `claude-cli usage open`

Open the Claude usage page in the browser for an account.

```bash
claude-cli usage open              # Current account
claude-cli usage open personal     # Specific account
```

---

### `claude-cli status`

Quick overview of all accounts — a dashboard view.

```bash
claude-cli status
```

```
                    Claude CLI Status
┏━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Account      ┃ Tier ┃ Auth       ┃ Status         ┃
┡━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ ● work       │ pro  │ ✓ valid    │ Active         │
│   personal   │ max  │ ✓ valid    │ Active         │
│   client-a   │ max  │ ✗ expired  │ Needs login    │
└──────────────┴──────┴────────────┴────────────────┘
  Active: work | 3 accounts configured
  Shared: settings ✓  rules ✓  agents ✓  MCP ✓

  Run "claude-cli use <name>" to switch.
  Run "claude-cli account login <name>" to re-authenticate.
```

---

### `claude-cli config`

Manage global CLI settings (not account-specific).

#### `claude-cli config show`

```bash
claude-cli config show
```

```
Global Configuration
  Config File:     ~/.claude-cli/config.yaml
  Shared Dir:      ~/.claude-cli/shared/
  Accounts Dir:    ~/.claude-cli/accounts/
  Default Account: work
  Total Accounts:  3
```

#### `claude-cli config path`

Print the config file path (useful for scripting).

```bash
claude-cli config path
# Output: /Users/haonv/.claude-cli/config.yaml
```

---

### `claude-cli history`

View CLI command history.

```bash
claude-cli history                # Last 20 commands
claude-cli history -n 50          # Last 50
claude-cli history --clear        # Clear history
```

---

## Global Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--version` | `-V` | Show version |
| `--output` | `-O` | Output format: `table` (default), `json` |
| `--verbose` | `-v` | Verbose output for debugging |

---

## Configuration

### Config Schema

```yaml
# ~/.claude-cli/config.yaml

accounts:
  work:
    label: "Work — Pro"
    tier: pro                        # pro | max | team | enterprise
    created_at: "2025-03-15T10:00:00Z"

  personal:
    label: "Personal — Max"
    tier: max
    created_at: "2025-03-01T08:30:00Z"

  client-a:
    label: "Client A — Max"
    tier: max
    created_at: "2025-03-20T14:15:00Z"

default: work                        # Active account name
```

### Pydantic Models

```python
class AccountConfig(BaseModel):
    label: str                       # Display name
    tier: Literal["pro", "max", "team", "enterprise"]
    created_at: datetime

class Config(BaseModel):
    accounts: dict[str, AccountConfig]   # name -> config
    default: str | None                  # Active account name
```

### Symlinked Items

When creating an account, these items are symlinked from `shared/` to the account directory:

```python
SYMLINKED_ITEMS = [
    "settings.json",        # Permissions, hooks, default model, env vars
    ".claude.json",         # MCP servers (user scope), theme, vim mode
    "CLAUDE.md",            # Personal instructions
    "rules",               # User-level path-specific rules (directory)
    "agents",              # User subagents (directory)
    "plans",               # Implementation plans (directory)
    "projects",            # Auto memory per project (directory)
]

# NOT symlinked (per-account):
# .credentials.json       # OAuth tokens — unique per account
```

---

## Project Structure

```
claude-cli/
├── pyproject.toml
├── README.md
├── Makefile
├── .gitignore
│
├── docs/
│   ├── CLI_DESIGN.md              # This file
│   ├── PROJECT_STRUCTURE.md       # Architecture details
│   └── EXAMPLES.md                # Usage examples
│
├── src/
│   └── claude_cli/
│       ├── __init__.py            # __version__ = "0.1.0"
│       ├── __main__.py            # python -m claude_cli
│       ├── main.py                # Typer app entry point
│       │
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── init.py            # claude-cli init
│       │   ├── account.py         # claude-cli account [list|add|remove|rename|login|current]
│       │   ├── use.py             # claude-cli use
│       │   ├── run.py             # claude-cli run
│       │   ├── usage.py           # claude-cli usage [show|open]
│       │   ├── status.py          # claude-cli status
│       │   ├── config.py          # claude-cli config [show|path]
│       │   └── history.py         # claude-cli history
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py          # Config load/save (~/.claude-cli/config.yaml)
│       │   ├── account.py         # Account CRUD, symlink management
│       │   ├── auth.py            # OAuth status check, login trigger
│       │   ├── usage.py           # Usage data fetching
│       │   └── history.py         # Command history
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── config.py          # Config, AccountConfig
│       │   └── usage.py           # UsageInfo, UsagePeriod
│       │
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── console.py         # Rich console, theme
│       │   ├── prompts.py         # Questionary wrappers
│       │   └── tables.py          # Rich table builders
│       │
│       └── utils/
│           ├── __init__.py
│           ├── validators.py      # Input validation
│           └── formatters.py      # Date/number formatting
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_commands/
    ├── test_core/
    └── test_models/
```

---

## Dependencies

```toml
[project]
requires-python = ">=3.10"

[project.dependencies]
typer = ">=0.12.0"
rich = ">=13.7.0"
questionary = ">=2.0.1"
pydantic = ">=2.6.0"
pyyaml = ">=6.0.1"
```

No heavy dependencies — the tool is a lightweight wrapper around Claude Code.

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error (no config, invalid account) |
| 3 | Authentication error (OAuth expired, login failed) |
| 4 | Account not found |
| 130 | User interrupt (Ctrl+C) |

---

## Command Summary

| Command | Description |
|---------|-------------|
| `claude-cli init` | Interactive setup wizard |
| `claude-cli account list` | List all accounts |
| `claude-cli account add` | Add new account |
| `claude-cli account remove <name>` | Remove account (credentials only, shared untouched) |
| `claude-cli account rename <old> <new>` | Rename account |
| `claude-cli account login [name]` | Re-authenticate account |
| `claude-cli account current` | Show active account |
| `claude-cli use [name]` | Switch active account |
| `claude-cli run [-- args...]` | Launch Claude Code with active account |
| `claude-cli run -a <name> [-- args...]` | Launch Claude Code with specific account |
| `claude-cli usage show [name\|--all]` | View usage info |
| `claude-cli usage open [name]` | Open usage page in browser |
| `claude-cli status` | Dashboard — all accounts overview |
| `claude-cli config show` | Show global config |
| `claude-cli config path` | Print config file path |
| `claude-cli history` | View command history |

---

## Implementation Checklist

### Phase 1: Foundation & Account Management

| # | Task | Files |
|---|------|-------|
| 1 | Project scaffold (`pyproject.toml`, `Makefile`, `.gitignore`) | root |
| 2 | Package entry point | `__init__.py`, `__main__.py`, `main.py` |
| 3 | Config Pydantic models | `models/config.py` |
| 4 | Config load/save | `core/config.py` |
| 5 | Rich console + theme | `ui/console.py` |
| 6 | Questionary prompts | `ui/prompts.py` |
| 7 | Table builders | `ui/tables.py` |
| 8 | Input validators | `utils/validators.py` |
| 9 | Account CRUD + symlink management | `core/account.py` |
| 10 | `claude-cli init` (with migration support) | `commands/init.py` |
| 11 | `claude-cli account list` | `commands/account.py` |
| 12 | `claude-cli account add` | `commands/account.py` |
| 13 | `claude-cli account remove` | `commands/account.py` |
| 14 | `claude-cli account rename` | `commands/account.py` |
| 15 | `claude-cli account current` | `commands/account.py` |

### Phase 2: Switch & Run

| # | Task | Files |
|---|------|-------|
| 16 | `claude-cli use` (interactive + direct) | `commands/use.py` |
| 17 | `claude-cli run` (exec claude with CLAUDE_CONFIG_DIR) | `commands/run.py` |
| 18 | `claude-cli account login` (trigger OAuth) | `commands/account.py`, `core/auth.py` |
| 19 | Auth status check (token validity) | `core/auth.py` |
| 20 | `claude-cli status` dashboard | `commands/status.py` |

### Phase 3: Usage & Polish

| # | Task | Files |
|---|------|-------|
| 21 | Usage data models | `models/usage.py` |
| 22 | Usage fetching logic | `core/usage.py` |
| 23 | `claude-cli usage show` | `commands/usage.py` |
| 24 | `claude-cli usage open` | `commands/usage.py` |
| 25 | `claude-cli config show` / `config path` | `commands/config.py` |
| 26 | Command history | `core/history.py`, `commands/history.py` |

### Phase Summary

| Phase | Items | Scope |
|-------|-------|-------|
| **Phase 1** | 15 | Foundation, models, account CRUD, symlinks |
| **Phase 2** | 5 | Switch, run, auth, status |
| **Phase 3** | 6 | Usage, config, history |
| **Total** | **26** | |