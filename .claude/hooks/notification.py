#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

import argparse
import os
import subprocess
import random
from pathlib import Path
import json
import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

TMP_FILE = (Path.cwd() / ".claude").expanduser()
TMP_FILE.mkdir(parents=True, exist_ok=True)
TMP_FILE = TMP_FILE / "tmp_last_event.json"


def get_tts_script_path():
    """
    Determine which TTS script to use based on available API keys.
    Priority order: ElevenLabs > OpenAI > pyttsx3
    """
    # Get current script directory and construct utils/tts path
    script_dir = Path(__file__).parent
    tts_dir = script_dir / "utils" / "tts"
    
    # Check for ElevenLabs API key (highest priority)
    if os.getenv('ELEVENLABS_API_KEY'):
        elevenlabs_script = tts_dir / "elevenlabs_tts.py"
        if elevenlabs_script.exists():
            return str(elevenlabs_script)
    
    # Check for OpenAI API key (second priority)
    if os.getenv('OPENAI_API_KEY'):
        openai_script = tts_dir / "openai_tts.py"
        if openai_script.exists():
            return str(openai_script)
    
    # Fall back to pyttsx3 (no API key required)
    pyttsx3_script = tts_dir / "pyttsx3_tts.py"
    if pyttsx3_script.exists():
        return str(pyttsx3_script)
    
    return None


def log_notification(stdin_payload: str):
    """Save latest notification payload and maybe speak it."""
    try:
        data = json.loads(stdin_payload)
        message = data.get("message") or data.get("text") or str(data)[:500]
        record = {"event": "Notification", "message": message, "ts": time.time()}
        # history append (keep 3)
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
        TMP_FILE.write_text(json.dumps(history))

        # If the notification is not the boring default, speak it immediately
        boring = [
            "Claude is waiting for your input",
            "Need input",
        ]
        if message and message.strip() not in boring:
            announce_notification(custom_message=message)
    except Exception:
        pass


def announce_notification(custom_message: str | None = None):
    """Announce with TTS; if custom_message provided use it."""
    try:
        tts_script = get_tts_script_path()
        if not tts_script:
            return

        if custom_message:
            notification_message = custom_message[:120]
        else:
            notification_message = "Task complete."
            engineer_name = os.getenv('ENGINEER_NAME', '').strip()
            if engineer_name and random.random() < 0.3:
                notification_message = f"{engineer_name}, task complete."

        subprocess.run([
            "uv", "run", tts_script, notification_message
        ], capture_output=True, timeout=10)
    except Exception:
        pass


def main():
    """
    If called from a hook (no --notify flag) we log stdin JSON.
    If --notify flag is passed, we also play TTS immediately.
    """
    try:
        stdin_data = sys.stdin.read()
        if stdin_data:
            log_notification(stdin_data)

        parser = argparse.ArgumentParser(description="Triggers a TTS notification.")
        parser.add_argument('--notify', action='store_true', help='Enable TTS playback immediately')
        args = parser.parse_args()

        if args.notify:
            announce_notification()
    except Exception:
        pass

if __name__ == '__main__':
    main()