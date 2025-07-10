#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
# ]
# ///

import argparse
import os
import sys
import json
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import our unified managers
sys.path.insert(0, str(Path(__file__).parent))
from utils.tts import TTSManager
from utils.llm import LLMManager

TMP_FILE = (Path.cwd() / ".claude").expanduser()
TMP_FILE.mkdir(parents=True, exist_ok=True)
TMP_FILE = TMP_FILE / "tmp_last_event.json"


def log_notification(stdin_payload: str):
    """Save latest notification payload and speak it using unified managers."""
    try:
        data = json.loads(stdin_payload)
        message = data.get("message") or data.get("text") or str(data)[:500]
        
        # Get recent completions for context
        recent_completion = get_latest_completion()
        
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

        # If the notification is not boring, speak it with enhancement
        boring = [
            "Claude is waiting for your input",
            "Need input",
        ]
        if message and message.strip() not in boring:
            announce_notification(recent_completion)
    except Exception:
        pass


def get_latest_completion():
    """Get the most recent tool completion info."""
    try:
        if TMP_FILE.exists():
            history = json.loads(TMP_FILE.read_text())
            if isinstance(history, list):
                # Find the most recent PostToolUse event
                for event in reversed(history):
                    if event.get("event") == "PostToolUse":
                        return event.get("info") or f"used {event.get('tool', 'tool')}"
    except Exception:
        pass
    return None


def announce_notification(tool_info: str = None):
    """Announce completion using unified TTS and LLM managers."""
    try:
        engineer_name = os.getenv('ENGINEER_NAME', '').strip() or None
        
        # Create managers
        llm = LLMManager()
        tts = TTSManager()
        
        # Enhance the message
        if tool_info:
            message = llm.enhance_completion_message(tool_info, engineer_name)
        else:
            message = llm.enhance_completion_message("task complete", engineer_name)
        
        # Speak the enhanced message
        tts.speak(message)
        
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