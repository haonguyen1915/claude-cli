# Changelog

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

