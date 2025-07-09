#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import sys
from pathlib import Path
import time

# Cache file now lives under the active project folder
PROJECT_CLAUDE_DIR = Path.cwd() / ".claude"
PROJECT_CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
TMP_FILE = PROJECT_CLAUDE_DIR / "tmp_last_event.json"


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

    # Build a compact record
    tool_name = payload.get("tool_name") or payload.get("tool", "unknown_tool")
    tool_resp = payload.get("tool_response", {}) or {}

    # raw may itself be str/list/whatever
    raw = None
    if isinstance(tool_resp, dict):
        raw = (
            tool_resp.get("stdout")
            or tool_resp.get("content")
            or tool_resp.get("stderr")
            or ""
        )
    else:
        raw = tool_resp

    snippet = _extract_text(raw).strip()[:500]

    record = {
        "event": "PostToolUse",
        "tool": tool_name,
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