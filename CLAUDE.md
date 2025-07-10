# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains Claude Code settings and configurations for macOS. It's a personal configuration repository that manages Claude Code permissions, hooks, and custom commands.

## Key Architecture

### Settings Configuration
- **`.claude/settings.json`**: Main configuration file containing:
  - Permissions for allowed Bash commands (mkdir, uv, find, mv, grep, npm, ls, cp, chmod, touch)
  - Write and Edit tool permissions
  - Hook configurations for PostToolUse, Notification, and Stop events

### Hooks System
- Hooks are Python scripts executed via `uv run` for various events
- **PostToolUse Hook**: Runs `~/.claude/hooks/post_tool_use.py` after tool usage
- **Notification Hook**: Runs `~/.claude/hooks/notification.py` for notifications  
- **Stop Hook**: Runs `~/.claude/hooks/stop.py` when stopping
- Hook logs are stored in `.claude/hooks/logs/`

### Custom Commands
- **UltraThink Command** (`.claude/commands/ultrathink.md`): A multi-agent coordination system
  - Usage: `/project:ultrathink <TASK_DESCRIPTION>`
  - Orchestrates four specialist sub-agents: Architect, Research, Coder, and Tester
  - Follows a structured process with reasoning transcript and actionable output

## Development Notes

- This is a configuration-only repository with no build process or tests
- Changes to settings require understanding the Claude Code permissions and hooks system
- The `uv` Python package manager is used for running hook scripts
- All hooks reference scripts in the global `~/.claude/hooks/` directory rather than local files