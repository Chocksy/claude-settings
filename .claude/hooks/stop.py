#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import os
import subprocess
import sys
import json
from pathlib import Path
import random
import time

# Location of the cached last-event file written by other hooks
TMP_FILE = (Path.cwd() / ".claude" / "tmp_last_event.json").expanduser()


def get_tts_script_path():
    """Same helper used in notification.py – returns best available TTS script."""
    script_dir = Path(__file__).parent
    tts_dir = script_dir / "utils" / "tts"

    if os.getenv("ELEVENLABS_API_KEY"):
        p = tts_dir / "elevenlabs_tts.py"
        if p.exists():
            return str(p)

    if os.getenv("OPENAI_API_KEY"):
        p = tts_dir / "openai_tts.py"
        if p.exists():
            return str(p)

    p = tts_dir / "pyttsx3_tts.py"
    if p.exists():
        return str(p)

    return None


def summarise_text(text: str) -> str:
    """Call existing utils/llm/oai.py to get <=10-word summary."""
    oai_script = Path(__file__).parent / "utils" / "llm" / "oai.py"
    if not oai_script.exists():
        return None

    prompt = f"Summarize in 10 words or fewer: {text}"
    try:
        summary = subprocess.check_output([
            "uv",
            "run",
            str(oai_script),
            prompt,
        ], text=True, timeout=30).strip()
        # guard — make sure not empty and reasonable length
        if summary:
            return summary.split("\n")[0].strip().strip('"').strip("'")
    except Exception:
        pass

    # Fallback: use --completion for generic message
    try:
        fallback = subprocess.check_output([
            "uv",
            "run",
            str(oai_script),
            "--completion",
        ], text=True, timeout=20).strip()
        return fallback or "Task complete"
    except Exception:
        return "Task complete"


def build_summary() -> str:
    if not TMP_FILE.exists():
        return "Task complete"

    try:
        history = json.loads(TMP_FILE.read_text())
        if not isinstance(history, list):
            history = [history]
    except Exception:
        return "Task complete"

    # pick last non-Notification if exists else last
    chosen = None
    for item in reversed(history):
        if item.get("event") != "Notification":
            chosen = item
            break
    if chosen is None:
        chosen = history[-1]

    if chosen.get("event") == "Notification":
        text = chosen.get("message", "Notification finished")
    else:
        tool = chosen.get("tool", "task")
        snippet = chosen.get("snippet", "")
        text = f"{tool} completed. {snippet}"

    return summarise_text(text)


def main():
    # Build message
    message = build_summary()

    tts_script = get_tts_script_path()
    if not tts_script:
        sys.exit(0)

    try:
        subprocess.run(["uv", "run", tts_script, message], capture_output=True, timeout=15)
    except Exception:
        pass


if __name__ == "__main__":
    main()
