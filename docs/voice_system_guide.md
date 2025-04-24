# JARVIS Enhanced Voice System Guide

This guide explains the enhanced voice system features in JARVIS, including both speech recognition and text-to-speech capabilities.

## Overview

JARVIS now offers multiple options for voice interaction:

1. **Native Speech Recognition** - Using Python-based libraries like SpeechRecognition, PyAudio, and PocketSphinx
2. **Web-Based Speech Recognition** - Using the browser's Web Speech API for improved accuracy
3. **Enhanced Natural Responses** - More conversational responses with acknowledgments, confirmations, and natural continuations
4. **Multiple TTS Options** - Support for pyttsx3, Google TTS, ElevenLabs, and Microsoft Edge TTS

## Speech Recognition Options

### Native Speech Recognition

The native speech recognition uses the Python SpeechRecognition library with multiple backend options:

- **Google Speech Recognition** - Requires internet connection, high accuracy
- **PocketSphinx** - Offline recognition, lower accuracy but works without internet
- **Other backends** - Support for Whisper, Google Cloud, Azure, etc. if configured

To use native speech recognition:

```python
from src.tools.voice_recognition import SpeechRecognition

# Initialize
speech = SpeechRecognition({"wake_word": "jarvis"})

# Start listening (provide a callback function to handle commands)
def on_command(command):
    print(f"Command received: {command}")

speech.start(on_command)
```

### Web-Based Speech Recognition

The web-based option uses the browser's Web Speech API, which often provides better accuracy and language support:

1. Start the web speech connector:

```python
from src.web.web_speech_connector import WebSpeechConnector

# Initialize and start
connector = WebSpeechConnector({"host": "127.0.0.1", "port": 5000})
connector.start(on_command)  # Same callback as above
```

2. Open the browser at `http://127.0.0.1:5000` to access the speech recognition interface
3. Click "Start Recognition" and speak commands
4. Commands will be sent back to your JARVIS system

## Text-to-Speech Options

### Standard Voice Engine

The standard voice engine supports multiple providers:

```python
from src.tools.voice_engine import VoiceEngine

# Initialize with provider of choice
voice = VoiceEngine(provider="pyttsx3")  # Options: pyttsx3, gtts, elevenlabs
voice.start()

# Speak text
voice.speak("Hello, I am JARVIS")

# Adjust properties
voice.set_rate(200)  # Speed
voice.set_volume(0.8)  # Volume
```

### Edge TTS Engine

For more natural-sounding voices, the Edge TTS Engine uses Microsoft's Edge TTS:

```python
import asyncio
from src.tools.edge_tts_engine import EdgeTTSEngine

async def test_edge_tts():
    # Initialize
    tts = EdgeTTSEngine({"voice": "en-US-GuyNeural"})
    await tts.start()
    
    # Speak text
    await tts.speak("Hello, I am JARVIS using Edge TTS")
    
    # List available voices
    voices = await tts.get_available_voices("en")
    print(f"Available voices: {voices}")
    
    # Change voice
    await tts.set_voice("en-US-AriaNeural")
    await tts.speak("Now I'm speaking with a different voice")

asyncio.run(test_edge_tts())
```

## Enhanced Voice System

The Enhanced Voice System combines recognition and synthesis with more natural interactions:

```python
import asyncio
from src.tools.enhanced_voice import EnhancedVoice

async def test_enhanced_voice():
    # Initialize
    voice_system = EnhancedVoice({
        "wake_word": "jarvis",
        "use_conversational_responses": True,
        "speaking_rate": 175
    })
    
    # Start the system with a command processor
    def process_command(cmd):
        print(f"Processing: {cmd}")
        voice_system.speak(f"You said: {cmd}")
    
    await voice_system.start(process_command)
    
    # The system will now listen for commands and respond

asyncio.run(test_enhanced_voice())
```

## Integrated Demo

For a complete demo of all voice features, run the test script:

```bash
python test_improved_jarvis.py
```

This will start JARVIS with:
- Enhanced voice recognition
- Web-based recognition interface
- Natural responses
- Edge TTS if available
- Integration with the knowledge base

## Command Examples

Here are some example commands to try:

- "JARVIS, hello"
- "JARVIS, what time is it?"
- "JARVIS, tell me about yourself"
- "JARVIS, what can you do?"
- "JARVIS, switch voice"
- "JARVIS, web interface"
- "JARVIS, help"

## Troubleshooting

If you encounter issues with the voice system:

1. Run the diagnostic tool: `python diagnose_voice.py --interactive`
2. Check that all required dependencies are installed:
   ```
   pip install SpeechRecognition pyaudio pocketsphinx pyttsx3 gTTS edge-tts pygame flask flask-cors
   ```
3. Ensure your microphone is working and properly connected
4. Try the web-based speech recognition as an alternative to native recognition

For issues with Edge TTS, make sure you have an internet connection as it requires online access. 