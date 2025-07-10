#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "elevenlabs",
#     "openai",
#     "pyttsx3",
#     "python-dotenv",
# ]
# ///

import os
import sys
import asyncio
import tempfile
import subprocess
import platform
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class TTSManager:
    """Unified TTS manager with automatic fallback between providers."""
    
    def __init__(self):
        self.elevenlabs_available = bool(os.getenv('ELEVENLABS_API_KEY'))
        self.openai_available = bool(os.getenv('OPENAI_API_KEY'))
        
    def speak(self, text: str) -> bool:
        """
        Speak text using the best available TTS provider.
        
        Args:
            text: Text to speak
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not text or not text.strip():
            return False
            
        text = text.strip()
        
        # Priority order: ElevenLabs → OpenAI → pyttsx3
        if self.elevenlabs_available:
            if self._speak_elevenlabs(text):
                return True
                
        if self.openai_available:
            if self._speak_openai(text):
                return True
                
        # Fallback to pyttsx3 (always available)
        return self._speak_pyttsx3(text)
    
    def _speak_elevenlabs(self, text: str) -> bool:
        """Speak using ElevenLabs TTS."""
        try:
            from elevenlabs.client import ElevenLabs
            from elevenlabs import play
            
            client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))
            
            audio = client.text_to_speech.convert(
                text=text,
                voice_id="SAz9YHcvj6GT2YYXdXww",
                model_id="eleven_turbo_v2_5",
                output_format="mp3_44100_128",
            )
            
            play(audio)
            return True
            
        except Exception:
            return False
    
    def _speak_openai(self, text: str) -> bool:
        """Speak using OpenAI TTS."""
        try:
            # Run async function in new event loop
            return asyncio.run(self._speak_openai_async(text))
        except Exception:
            return False
    
    async def _speak_openai_async(self, text: str) -> bool:
        """Async implementation for OpenAI TTS."""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            response = await client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="nova",
                input=text,
                instructions="Speak in a cheerful, positive yet professional tone.",
                response_format="mp3",
            )
            
            # Save to temp file and play
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            # Play using system audio player
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["afplay", temp_file_path], 
                             check=True, capture_output=True)
            elif system == "Linux":
                subprocess.run(["aplay", temp_file_path], 
                             check=True, capture_output=True)
            elif system == "Windows":
                subprocess.run(["start", temp_file_path], 
                             shell=True, check=True, capture_output=True)
            
            # Clean up
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
            return True
            
        except Exception:
            return False
    
    def _speak_pyttsx3(self, text: str) -> bool:
        """Speak using pyttsx3 (offline fallback)."""
        try:
            import pyttsx3
            
            engine = pyttsx3.init()
            engine.setProperty('rate', 180)
            engine.setProperty('volume', 0.8)
            
            engine.say(text)
            engine.runAndWait()
            return True
            
        except Exception:
            return False


def main():
    """CLI interface for testing."""
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        tts = TTSManager()
        success = tts.speak(text)
        if not success:
            print("Failed to speak text")
            sys.exit(1)
    else:
        print("Usage: ./tts.py 'text to speak'")


if __name__ == "__main__":
    main()