# Claude Code Hooks Setup (macOS)

## Overview
This repository provides a ready-to-use set of **Claude Code hooks** that extend Anthropic’s Claude Code assistant with deterministic automation, desktop/voice notifications, and friendly completion messages.

Hooks are small shell commands (here implemented as Python scripts executed via the ultra-fast **uv** runner) that Claude Code triggers automatically at key moments:

* **PreToolUse** – before Claude runs a tool (not used in this repo)
* **PostToolUse** – right after a tool completes (we log the result)
* **Notification** – whenever Claude sends a notification (we speak + banner it)
* **Stop** – when Claude finishes responding (we deliver a succinct voice summary)

---

## Prerequisites
1. **macOS 14 (Sonoma) or later**
2. **Python ≥ 3.11** (pre-installed on macOS 14, or install via Homebrew)
3. **uv** — ultra-fast package manager/runner used by every hook script
   ```bash
   brew install astral-sh/uv/uv
   ```
4. *(Optional)* **jq** for advanced logging examples
   ```bash
   brew install jq
   ```

---

## Required Environment Variables
Create a `.env` file in your HOME directory **or** export the variables in your shell profile (`~/.zshrc`, `~/.bash_profile`).

```dotenv
# Claude / Anthropic
ANTHROPIC_API_KEY="sk-ant-…"

# OpenAI (used for LLM & optional TTS)
OPENAI_API_KEY="sk-oai-…"

# ElevenLabs (optional high-quality TTS)
ELEVENLABS_API_KEY="elevenlabs-…"

# Personalisation (optional)
ENGINEER_NAME="Your Name"
```
Then reload your shell:
```bash
source ~/.zshrc   # or ~/.bash_profile
```

> Tip 👀 : Keep API keys in your macOS Keychain or a secrets manager. Do **not** commit them to git.

---

## Installation Options
Choose **one** of the following.

### 1 · Project-local hooks (recommended per-repo)
```bash
# From inside your project root
cp -R path/to/claude-settings/.claude .
```
* Commit the copied `.claude/` directory to version control so teammates inherit the same behaviour.
* Edit `.claude/settings.json` to tweak matchers or commands.

### 2 · Global hooks (apply to every Claude Code project)
```bash
mkdir -p ~/.claude
cp -R path/to/claude-settings/.claude/* ~/.claude/
```
* Global hooks live in `~/.claude/settings.json` and override/merge with per-project settings.
* Symlinks also work if you prefer: `ln -s "$PWD/.claude" ~/.claude`.

---

## Step-by-Step Setup
1. **Install prerequisites** (`uv`, `python`, `jq`).
2. **Clone this repo** or download the `.claude` folder.
3. **Pick local or global installation** (see above) and copy files.
4. **Set environment variables** in `.env` or your shell profile.
5. **Reload Claude Code hooks**:
   * Open Claude Code REPL (⌘⇧P ➜ `>Hooks`) or simply type `/hooks`.
   * Press <kbd>Esc</kbd> to apply the new configuration.
6. *(Optional)* restart Claude Code to ensure fresh environment variables are detected.

---

## Testing Your Hooks
1. **PostToolUse** – Edit any file inside Claude Code:
   *Expected*: A banner + voice message like “File updated!”
2. **Notification** – Run a long Bash command (`sleep 5`):
   *Expected*: Voice message when Claude needs input.
3. **Stop** – Finish a conversation / let Claude respond completely:
   *Expected*: Short spoken summary (“Task complete”).

Check `.claude/tmp_last_event.json` for the last few events if something seems off.

---

## Troubleshooting
| Issue | Fix |
|-------|-----|
| `uv: command not found` | Re-install via Homebrew and ensure `/opt/homebrew/bin` is in `$PATH`. |
| No voice output | Verify `ELEVENLABS_API_KEY` or `OPENAI_API_KEY` is set; fallback uses macOS `afplay`. |
| Hooks not running | Run `/hooks` and confirm your settings appear; ensure JSON syntax is valid. |
| `Permission denied` on scripts | `chmod +x .claude/hooks/**/*.py` to make scripts executable. |

---

## Security Notes
Claude Code executes hook commands **automatically with your user permissions**. Malicious or buggy commands can delete files, leak secrets, or brick your system. Follow best practices:
* Understand every command you add.
* Quote shell variables (`"$VAR"`).
* Use absolute paths where practical.
* Skip sensitive files in your matchers.

*(Adapted from Anthropic’s official security disclaimer.)*

---

## References & Further Reading
* Anthropic Docs – Hooks: <https://docs.anthropic.com/en/docs/claude-code/hooks>
* Cherry Zhou, “Claude Code’s Hooks Feature” (Medium) – <https://medium.com/@CherryZhouTech/claude-codes-hooks-feature-unleashes-new-ai-programming-horizons-9d21d07e05fc>
* Joe Njenga, “How I’m Using Claude Code Hooks to Fully Automate My Workflow” – <https://medium.com/@joe.njenga/use-claude-code-hooks-newest-feature-to-fully-automate-your-workflow-341b9400cfbe>

Happy automated coding 🚀 