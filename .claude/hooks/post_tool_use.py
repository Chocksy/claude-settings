#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import sys
from pathlib import Path
import time
from utils.transcript import read_last_messages

# Cache file now lives under the active project folder
PROJECT_CLAUDE_DIR = Path.cwd() / ".claude"
PROJECT_CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
TMP_FILE = PROJECT_CLAUDE_DIR / "tmp_last_event.json"


def _extract_meaningful_info(tool_name, tool_input, tool_response):
    """Extract meaningful completion information based on tool type."""
    info_parts = []
    
    # Add tool-specific context from input
    if tool_name == "Edit" and tool_input:
        file_path = tool_input.get("file_path", "")
        if file_path:
            info_parts.append(f"edited {file_path}")
    elif tool_name == "Write" and tool_input:
        file_path = tool_input.get("file_path", "")
        if file_path:
            info_parts.append(f"wrote {file_path}")
    elif tool_name == "Read" and tool_input:
        file_path = tool_input.get("file_path", "")
        if file_path:
            info_parts.append(f"read {file_path}")
    elif tool_name == "Bash" and tool_input:
        command = tool_input.get("command", "")
        description = tool_input.get("description", "")
        if description:
            info_parts.append(f"ran: {description}")
        elif command:
            info_parts.append(f"ran: {command[:50]}")
    elif tool_name == "TodoWrite" and tool_input:
        todos = tool_input.get("todos", [])
        if todos:
            completed_count = len([t for t in todos if t.get("status") == "completed"])
            total_count = len(todos)
            info_parts.append(f"updated todos ({completed_count}/{total_count} completed)")
    elif tool_name == "Glob" and tool_input:
        pattern = tool_input.get("pattern", "")
        if pattern:
            info_parts.append(f"found files matching '{pattern}'")
    elif tool_name == "Grep" and tool_input:
        pattern = tool_input.get("pattern", "")
        if pattern:
            info_parts.append(f"searched for '{pattern}'")
    elif tool_name == "Task" and tool_input:
        description = tool_input.get("description", "")
        if description:
            info_parts.append(f"completed task: {description}")
    elif tool_name == "MultiEdit" and tool_input:
        file_path = tool_input.get("file_path", "")
        edits = tool_input.get("edits", [])
        if file_path and edits:
            info_parts.append(f"made {len(edits)} edits to {file_path}")
    elif tool_name == "LS" and tool_input:
        path = tool_input.get("path", "")
        if path:
            info_parts.append(f"listed contents of {path}")
    elif tool_name == "WebFetch" and tool_input:
        url = tool_input.get("url", "")
        if url:
            domain = url.split("//")[-1].split("/")[0] if "//" in url else url.split("/")[0]
            info_parts.append(f"fetched content from {domain}")
    
    # Add meaningful response info
    if isinstance(tool_response, dict):
        if "output" in tool_response:
            output = str(tool_response["output"]).strip()
            if output and len(output) > 10:
                # For file operations, show success/failure
                if tool_name in ["Edit", "Write"] and "successfully" in output.lower():
                    info_parts.append("✓ success")
                elif output:
                    info_parts.append(f"→ {output[:100]}")
        elif "content" in tool_response:
            content = str(tool_response["content"]).strip()
            if content:
                lines = content.count('\n') + 1
                chars = len(content)
                info_parts.append(f"→ {lines} lines, {chars} chars")
    
    return " | ".join(info_parts) if info_parts else f"completed {tool_name}"


def _extract_text(val):
    """Convert arbitrary json value to readable string."""
    if isinstance(val, str):
        return val
    if isinstance(val, list):
        parts = [_extract_text(v) for v in val]
        return " ".join(parts)
    if isinstance(val, dict):
        # common Claude blocks have 'text'
        if "text" in val and isinstance(val["text"], str):
            return val["text"]
        return json.dumps(val)
    return str(val)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # invalid or empty stdin
        sys.exit(0)

    # Build a detailed record with meaningful information
    tool_name = payload.get("tool_name") or payload.get("tool", "unknown_tool")
    tool_input = payload.get("tool_input", {})
    tool_resp = payload.get("tool_response", {}) or {}
    transcript_path = payload.get("transcript_path")

    # Extract meaningful completion info
    meaningful_info = _extract_meaningful_info(tool_name, tool_input, tool_resp)

    snippet = ""
    if transcript_path:
        snippet = read_last_messages(transcript_path, max_lines=20, max_chars=200)

    record = {
        "event": "PostToolUse",
        "tool": tool_name,
        "info": meaningful_info,
        "snippet": snippet,
        "ts": time.time()
    }

    # load existing history list
    history = []
    if TMP_FILE.exists():
        try:
            history = json.loads(TMP_FILE.read_text())
            if not isinstance(history, list):
                history = []
        except Exception:
            history = []

    history.append(record)
    history = history[-3:]

    try:
        TMP_FILE.write_text(json.dumps(history))
    except Exception:
        pass

    # exit quietly
    sys.exit(0)


if __name__ == "__main__":
    main()