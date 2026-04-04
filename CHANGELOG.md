# Changelog

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

