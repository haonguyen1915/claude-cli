# Changelog

## [0.1.7] - 2026-06-29

### Release Notes

### What's Changed
- Improved installation process by automatically detecting Claude in common directories when not found on the path.

### Bug Fixes

- fix: fall back to common install dirs when claude not on path (d31b62e)

**Contributors:** @Nguyễn Văn Hảo

**Compare changes:** [v0.1.6...v0.1.7](https://github.com/haonguyen1915/claude-cli.git/-/compare/v0.1.6...v0.1.7)

## [0.1.6] - 2026-06-25

### Release Notes

Improved configuration management for user accounts.

### What's Changed
- Ensured .claude.json configuration is correctly maintained per account for accurate status display.
- Automatically seeded missing JSON configuration files with an empty object to prevent errors.

### Bug Fixes

- fix: keep .claude.json per-account so status shows correct account (7fd7c3b)
- fix: seed missing json config files with empty object (fc2e71b)

**Contributors:** @Nguyễn Văn Hảo

**Compare changes:** [v0.1.5...v0.1.6](https://github.com/haonguyen1915/claude-cli.git/-/compare/v0.1.5...v0.1.6)

## [0.1.5] - 2026-06-11

### Release Notes

### What's Changed
- Implemented fallback to junction/hardlink when Windows symlink creation fails, improving compatibility.

### Bug Fixes

- fix: fall back to junction/hardlink on windows symlink failure (52814ef)

**Contributors:** @Nguyễn Văn Hảo

**Compare changes:** [v0.1.4...v0.1.5](https://github.com/haonguyen1915/claude-cli.git/-/compare/v0.1.4...v0.1.5)

## [0.1.4] - 2026-05-26

### Release Notes

### What's Changed
- Ensured compatibility with questionary by pinning prompt-toolkit version.

### Bug Fixes

- fix: pin prompt-toolkit version for questionary compatibility (38f4d80)

**Contributors:** @Nguyễn Văn Hảo

**Compare changes:** [v0.1.3...v0.1.4](https://github.com/haonguyen1915/claude-cli.git/-/compare/v0.1.3...v0.1.4)

## [0.1.3] - 2026-04-07

### Release Notes

Enhanced command functionality and improved token management.

### What's Changed
- Replaced account rename functionality with a more versatile update command.
- Improved token management by forcing refresh and auto-login on failure.
- Fixed issues with API refresh token handling.
- Resolved unicode display issues in terminal.

### Features

- feat: replace account rename with update command (aaf7dff)

### Bug Fixes

- fix: force refresh all tokens and auto-login on failure (111aa7b)
- fix: API refresh token (36cc046)
- fix: unicode in terminal (0acd9cd)

**Contributors:** @Nguyễn Văn Hảo

**Compare changes:** [v0.1.2...v0.1.3](https://github.com/haonguyen1915/claude-cli.git/-/compare/v0.1.2...v0.1.3)

## [0.1.2] - 2026-04-04

### Release Notes

Enhanced usage monitoring and token management.

### What's Changed
- Persisted usage cache to file for improved cross-session performance.
- Introduced live watch mode for real-time usage monitoring.
- Implemented auto-refresh for expiring tokens during live monitoring.
- Enhanced rate-limit handling with usage cache and safe fetching.

### Features

- feat: persist usage cache to file for cross-session reuse (f82030c)
- feat: add usage cache on rate limit, status column, and rate-limit-safe fetching (ed3a9e9)
- feat: auto-refresh expiring tokens during live usage monitoring (fb7fba7)
- feat: add live watch mode for usage monitoring (13201d0)

### Bug Fixes

- fix: rename cc alias to ccc to avoid system cc conflict (8f132fa)

### Documentation

- docs: improve README with badges, changelog link, and make commands (8092dad)

**Contributors:** @Nguyễn Văn Hảo

**Compare changes:** [v0.1.1...v0.1.2](https://github.com/haonguyen1915/claude-cli.git/-/compare/v0.1.1...v0.1.2)

## [0.1.1] - 2026-04-04

### Release Notes

Enhanced authentication and monitoring capabilities.

### What's Changed
- Introduced live usage monitoring through the Anthropic OAuth API for real-time insights.
- Implemented token expiry checks from the keychain to ensure accurate authentication status.
- Added new command aliasing and restructured run commands for improved usability.
- Enabled sharing of commands, skills, sessions, and history across accounts for better collaboration.

### Features

- feat: add cc alias and restructure run commands (0b0b72f)
- feat: check token expiry from keychain for accurate auth status (9a01d41)
- feat: add live usage monitoring via Anthropic OAuth API (a874438)
- feat: add commands/skills sharing and account repair command (7e57d6c)
- feat: initial implementation of claude-cli (6cfbb46)

### Refactoring

- refactor: simplify symlinks to link all items directly to ~/.claude (7025770)

**Contributors:** @Nguyễn Văn Hảo

