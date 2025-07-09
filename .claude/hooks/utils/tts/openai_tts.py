#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "openai",
#     "openai[voice_helpers]",
#     "python-dotenv",
# ]
# ///

import os
import sys
import asyncio
import tempfile
from pathlib import Path
from dotenv import load_dotenv


async def main():
    """
    OpenAI TTS Script

    Uses OpenAI's latest TTS model for high-quality text-to-speech.
    Accepts optional text prompt as command-line argument.

    Usage:
    - ./openai_tts.py                    # Uses default text
    - ./openai_tts.py "Your custom text" # Uses provided text

    Features:
    - OpenAI gpt-4o-mini-tts model (latest)
    - Nova voice (engaging and warm)
    - Saves audio to file first, then plays (fixes white noise issue)
    - Fallback to system audio player if LocalAudioPlayer fails
    """

    # Load environment variables
    load_dotenv()

    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please add your OpenAI API key to .env file:")
        print("OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)

    try:
        from openai import AsyncOpenAI
        from openai.helpers import LocalAudioPlayer

        # Initialize OpenAI client
        openai = AsyncOpenAI(api_key=api_key)

        print("🎙️  OpenAI TTS")
        print("=" * 20)

        # Get text from command line argument or use default
        if len(sys.argv) > 1:
            text = " ".join(sys.argv[1:])  # Join all arguments as text
        else:
            text = "Today is a wonderful day to build something people love!"

        print(f"🎯 Text: {text}")
        print("🔊 Generating audio...")

        try:
            # Generate audio using OpenAI TTS (non-streaming)
            response = await openai.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="nova",
                input=text,
                instructions="Speak in a cheerful, positive yet professional tone.",
                response_format="mp3",
            )

            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name

            print(f"💾 Audio saved to: {temp_file_path}")
            print("🎵 Playing audio...")

            # Try LocalAudioPlayer first, fallback to system player
            try:
                # Read the file and play with LocalAudioPlayer
                with open(temp_file_path, 'rb') as audio_file:
                    await LocalAudioPlayer().play(audio_file)
                print("✅ Playback complete!")
            except Exception as player_error:
                print(f"⚠️  LocalAudioPlayer failed: {player_error}")
                print("🔄 Trying system audio player...")
                
                # Fallback to system audio player
                import subprocess
                import platform
                
                system = platform.system()
                if system == "Darwin":  # macOS
                    subprocess.run(["afplay", temp_file_path], check=True)
                elif system == "Linux":
                    subprocess.run(["aplay", temp_file_path], check=True)
                elif system == "Windows":
                    subprocess.run(["start", temp_file_path], shell=True, check=True)
                else:
                    print(f"❌ No audio player found for {system}")
                    print(f"Audio file saved at: {temp_file_path}")
                
                print("✅ Playback complete!")

            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
                print("🧹 Temporary file cleaned up")
            except:
                pass

        except Exception as e:
            print(f"❌ Error: {e}")

    except ImportError as e:
        print("❌ Error: Required package not installed")
        print("This script uses UV to auto-install dependencies.")
        print("Make sure UV is installed: https://docs.astral.sh/uv/")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
