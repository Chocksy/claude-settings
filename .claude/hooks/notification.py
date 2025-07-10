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
from utils.transcript import read_last_messages

TMP_FILE = (Path.cwd() / ".claude").expanduser()
TMP_FILE.mkdir(parents=True, exist_ok=True)
TMP_FILE = TMP_FILE / "tmp_last_event.json"


def log_notification(stdin_payload: str):
    """Save latest notification payload and speak it using unified managers."""
    try:
        data = json.loads(stdin_payload)
        message = data.get("message") or data.get("text") or str(data)[:1500]
        
        # Get recent completions for context from aggregated events
        recent_events = get_recent_events()
        
        # DEBUG: Log what we received + environment check
        engineer_env = os.getenv('ENGINEER_NAME')
        user_env = os.getenv('USER')
        home_env = os.getenv('HOME')
        debug_log = f"DEBUG notification.py: events={len(recent_events)}, message='{message}', ENGINEER_NAME='{engineer_env}', USER='{user_env}', HOME='{home_env}'"
        with open(".claude/hooks/logs/notification_debug.log", "a") as f:
            f.write(f"{time.time()}: {debug_log}\n")
        
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

        # Always announce with context when we have recent events
        if recent_events:
            announce_notification_with_context(recent_events)
    except Exception:
        pass


def get_recent_events():
    """Get recent events from tmp_last_event.json with transcript context."""
    try:
        if TMP_FILE.exists():
            history = json.loads(TMP_FILE.read_text())
            if isinstance(history, list):
                return history[-3:]  # Get last 3 events
    except Exception:
        pass
    return []

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


def announce_notification_with_context(recent_events: list):
    """Generate and speak a smart summary from recent events and transcript."""
    try:
        if not recent_events:
            return
            
        # Extract clean tool summaries from recent events
        tool_summaries = []
        
        for event in recent_events:
            if event.get("info"):
                tool_summaries.append(event["info"])
        
        engineer_name = os.getenv('ENGINEER_NAME', '').strip() or None
        
        # DEBUG: Log engineer name
        debug_log = f"DEBUG: engineer_name='{engineer_name}', env_check='{os.getenv('ENGINEER_NAME')}'"
        with open(".claude/hooks/logs/notification_debug.log", "a") as f:
            f.write(f"{time.time()}: {debug_log}\n")
        
        # Create smart summary
        llm = LLMManager()
        tts = TTSManager()
        
        # Focus on clean tool actions
        context = f"Recent actions completed: {'; '.join(tool_summaries[-3:])}"
        
        message = llm.enhance_completion_message(context, engineer_name)
        tts.speak(message)
        
    except Exception as e:
        # Fallback to simple announcement
        try:
            tts = TTSManager()
            tts.speak("Task completed")
        except Exception:
            pass

def announce_notification(tool_info: str = None, transcript_path: str = None):
    """Announce completion using unified TTS and LLM managers."""
    try:
        engineer_name = os.getenv('ENGINEER_NAME', '').strip() or None
        
        # Create managers
        llm = LLMManager()
        tts = TTSManager()
        
        context_snippet = ""
        if transcript_path:
            # DEBUG: Log transcript reading attempt
            debug_log = f"DEBUG: Attempting to read transcript at: {transcript_path}"
            with open(".claude/hooks/logs/notification_debug.log", "a") as f:
                f.write(f"{time.time()}: {debug_log}\n")
            
            context_snippet = read_last_messages(transcript_path, max_lines=100, max_chars=2000)
            
            # DEBUG: Log what we read
            debug_log = f"DEBUG: Read {len(context_snippet) if context_snippet else 0} chars from transcript"
            with open(".claude/hooks/logs/notification_debug.log", "a") as f:
                f.write(f"{time.time()}: {debug_log}\n")
                f.write(f"{time.time()}: TRANSCRIPT_CONTENT: {context_snippet[:200]}...\n")

        # Enhance the message
        base_info = tool_info or context_snippet or "task complete"
        message = llm.enhance_completion_message(base_info, engineer_name)
        
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