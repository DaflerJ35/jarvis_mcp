#!/usr/bin/env python3
"""
JARVIS Edge TTS Engine

This module provides text-to-speech capabilities using Microsoft Edge TTS,
offering high-quality voice synthesis with multiple voices.
"""

import os
import sys
import asyncio
import logging
import tempfile
import random
import pygame
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JarvisEdgeTTS")

# Try to import edge_tts
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    logger.warning("edge_tts not found. Install with: pip install edge-tts")
    EDGE_TTS_AVAILABLE = False

# Try to import pygame for audio playback
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    logger.warning("pygame not found. Install with: pip install pygame")
    PYGAME_AVAILABLE = False
except Exception as e:
    logger.warning(f"Error initializing pygame mixer: {e}")
    PYGAME_AVAILABLE = False

class EdgeTTSEngine:
    """
    Text-to-speech engine using Microsoft Edge TTS.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the Edge TTS engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.active = False
        
        # Default settings
        self.settings = {
            "voice": self.config.get("voice", "en-US-GuyNeural"),
            "rate": self.config.get("rate", "+0%"),  # -100% to +100%
            "volume": self.config.get("volume", "+0%"),  # -100% to +100%
            "pitch": self.config.get("pitch", "+0%"),  # -100% to +100%
            "cache_dir": self.config.get("cache_dir", "temp/tts_cache"),
            "use_cache": self.config.get("use_cache", True),
            "allow_special_chars": self.config.get("allow_special_chars", True)
        }
        
        # Special character filter
        self.allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890 :,.?!-_()[]{}'\""
        
        # Set up cache directory if enabled
        if self.settings["use_cache"]:
            os.makedirs(self.settings["cache_dir"], exist_ok=True)
        
        # Initialize the available voices list
        self.available_voices = []
        
        # Speaking state
        self.currently_speaking = False
        self.speech_queue = asyncio.Queue()
        self.current_speech_task = None
    
    async def start(self):
        """
        Start the TTS engine.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if not EDGE_TTS_AVAILABLE:
            logger.error("Edge TTS is not available. Please install edge-tts.")
            return False
            
        if not PYGAME_AVAILABLE:
            logger.error("Pygame is not available. Please install pygame for audio playback.")
            return False
        
        try:
            # Get available voices
            self.available_voices = await edge_tts.list_voices()
            logger.info(f"Found {len(self.available_voices)} Edge TTS voices")
            
            # Check if selected voice is available
            if not any(v["ShortName"] == self.settings["voice"] for v in self.available_voices):
                # Default to a standard voice if selected voice not available
                self.settings["voice"] = "en-US-GuyNeural"
                logger.warning(f"Selected voice not available. Using {self.settings['voice']} instead.")
            
            # Start the speech processing task
            self.active = True
            asyncio.create_task(self._process_speech_queue())
            
            logger.info(f"Edge TTS engine started with voice: {self.settings['voice']}")
            return True
        
        except Exception as e:
            logger.error(f"Error starting Edge TTS engine: {e}")
            return False
    
    async def stop(self):
        """
        Stop the TTS engine.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.active:
            return True
        
        try:
            # Stop the queue processing
            self.active = False
            
            # Cancel current speech if any
            if self.current_speech_task and not self.current_speech_task.done():
                self.current_speech_task.cancel()
            
            # Clear the queue
            while not self.speech_queue.empty():
                try:
                    await self.speech_queue.get_nowait()
                    self.speech_queue.task_done()
                except asyncio.QueueEmpty:
                    break
            
            logger.info("Edge TTS engine stopped")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping Edge TTS engine: {e}")
            return False
    
    async def _process_speech_queue(self):
        """Process the speech queue in the background."""
        while self.active:
            try:
                # Get the next speech item from the queue
                text, interrupt = await self.speech_queue.get()
                
                # If interrupt is True, cancel current speech
                if interrupt and self.current_speech_task and not self.current_speech_task.done():
                    self.current_speech_task.cancel()
                
                # Mark as speaking
                self.currently_speaking = True
                
                # Generate and play speech
                self.current_speech_task = asyncio.create_task(self._speak_text(text))
                await self.current_speech_task
                
                # Mark as done speaking
                self.currently_speaking = False
                
                # Mark the task as done
                self.speech_queue.task_done()
            
            except asyncio.CancelledError:
                # Task was cancelled
                self.currently_speaking = False
                logger.debug("Speech task cancelled")
            
            except Exception as e:
                logger.error(f"Error processing speech queue: {e}")
                self.currently_speaking = False
                # Small delay to avoid tight loop in case of errors
                await asyncio.sleep(0.1)
    
    async def _speak_text(self, text):
        """
        Generate speech for text and play it.
        
        Args:
            text: Text to convert to speech
        """
        if not EDGE_TTS_AVAILABLE or not PYGAME_AVAILABLE:
            logger.error("Cannot speak - TTS components not available")
            return
        
        # Clean the text if needed
        if not self.settings["allow_special_chars"]:
            text = self._remove_special_chars(text)
        
        # Short texts might be cached
        cache_file = None
        if self.settings["use_cache"] and len(text) < 500:
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            cache_file = os.path.join(self.settings["cache_dir"], f"{text_hash}.mp3")
            
            # If cache file exists, play it directly
            if os.path.exists(cache_file):
                logger.debug(f"Using cached speech for: {text[:30]}...")
                self._play_audio_file(cache_file)
                return
        
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            temp_filename = tmp_file.name
        
        try:
            # Configure the communicate class with voice settings
            communicate = edge_tts.Communicate(
                text,
                self.settings["voice"],
                rate=self.settings["rate"],
                volume=self.settings["volume"],
                pitch=self.settings["pitch"]
            )
            
            # Save audio to the temporary file
            await communicate.save(temp_filename)
            
            # Save to cache if enabled
            if cache_file and self.settings["use_cache"]:
                import shutil
                shutil.copy(temp_filename, cache_file)
            
            # Play the audio file
            self._play_audio_file(temp_filename)
        
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
        
        finally:
            # Remove temporary file
            try:
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
            except Exception as e:
                logger.error(f"Error removing temporary file: {e}")
    
    def _play_audio_file(self, file_path):
        """
        Play an audio file using pygame.
        
        Args:
            file_path: Path to the audio file
        """
        if not PYGAME_AVAILABLE:
            logger.error("Cannot play audio - pygame not available")
            return
        
        try:
            # Initialize the mixer if it's not already
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            # Load and play the audio
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Wait for the audio to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        
        except Exception as e:
            logger.error(f"Error playing audio file: {e}")
    
    def _remove_special_chars(self, text):
        """
        Remove special characters from text.
        
        Args:
            text: Text to clean
            
        Returns:
            str: Cleaned text
        """
        return ''.join(c for c in text if c in self.allowed_chars)
    
    async def speak(self, text, interrupt=False):
        """
        Add text to the speech queue.
        
        Args:
            text: Text to speak
            interrupt: Whether to interrupt current speech
            
        Returns:
            bool: True if added to queue, False otherwise
        """
        if not self.active:
            logger.warning("Cannot speak - TTS engine is not active")
            return False
        
        try:
            # Add to the queue
            await self.speech_queue.put((text, interrupt))
            return True
        
        except Exception as e:
            logger.error(f"Error adding text to speech queue: {e}")
            return False
    
    async def get_available_voices(self, locale=None):
        """
        Get a list of available voices.
        
        Args:
            locale: Optional locale filter (e.g., 'en-US')
            
        Returns:
            list: List of available voice names
        """
        if not EDGE_TTS_AVAILABLE:
            logger.error("Edge TTS is not available")
            return []
        
        try:
            # Refresh the list of voices
            self.available_voices = await edge_tts.list_voices()
            
            # Filter by locale if specified
            if locale:
                voices = [v for v in self.available_voices if v["Locale"].startswith(locale)]
            else:
                voices = self.available_voices
            
            # Return just the short names
            return [v["ShortName"] for v in voices]
        
        except Exception as e:
            logger.error(f"Error getting available voices: {e}")
            return []
    
    async def set_voice(self, voice_name):
        """
        Set the voice to use for speech.
        
        Args:
            voice_name: Name of the voice to use
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.active:
            logger.warning("Cannot set voice - TTS engine is not active")
            return False
        
        try:
            # Check if voice is available
            available_voices = await self.get_available_voices()
            
            if voice_name in available_voices:
                self.settings["voice"] = voice_name
                logger.info(f"Voice set to: {voice_name}")
                return True
            else:
                logger.warning(f"Voice '{voice_name}' not available")
                return False
        
        except Exception as e:
            logger.error(f"Error setting voice: {e}")
            return False
    
    async def set_rate(self, rate):
        """
        Set the speech rate.
        
        Args:
            rate: Speech rate value (-100 to 100)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert to percentage string format
            rate_value = max(-100, min(100, rate))
            if rate_value >= 0:
                self.settings["rate"] = f"+{rate_value}%"
            else:
                self.settings["rate"] = f"{rate_value}%"
            
            logger.info(f"Speech rate set to: {self.settings['rate']}")
            return True
        
        except Exception as e:
            logger.error(f"Error setting speech rate: {e}")
            return False
    
    async def set_volume(self, volume):
        """
        Set the speech volume.
        
        Args:
            volume: Volume value (-100 to 100)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert to percentage string format
            volume_value = max(-100, min(100, volume))
            if volume_value >= 0:
                self.settings["volume"] = f"+{volume_value}%"
            else:
                self.settings["volume"] = f"{volume_value}%"
            
            logger.info(f"Speech volume set to: {self.settings['volume']}")
            return True
        
        except Exception as e:
            logger.error(f"Error setting speech volume: {e}")
            return False


# For testing
async def main():
    """Test the Edge TTS engine"""
    print("Testing Edge TTS Engine")
    
    tts_engine = EdgeTTSEngine()
    success = await tts_engine.start()
    
    if not success:
        print("Failed to start Edge TTS engine")
        return
    
    # List available voices
    voices = await tts_engine.get_available_voices("en")
    print(f"Available English voices: {voices[:5]}... (showing 5 of {len(voices)})")
    
    # Speak a test message
    print("Speaking test message...")
    await tts_engine.speak("Hello, I am the Edge TTS engine for JARVIS. This is a test of my speech capabilities.")
    
    # Wait for speech to complete
    await asyncio.sleep(5)
    
    # Test with different voice
    if len(voices) > 1:
        print(f"Switching to voice: {voices[1]}")
        await tts_engine.set_voice(voices[1])
        await tts_engine.speak("Now I'm speaking with a different voice.")
        await asyncio.sleep(3)
    
    # Test with different rate
    print("Testing different speech rate...")
    await tts_engine.set_rate(30)  # Faster
    await tts_engine.speak("Now I'm speaking a bit faster.")
    await asyncio.sleep(3)
    
    # Reset rate and test interruption
    await tts_engine.set_rate(0)
    print("Testing speech interruption...")
    await tts_engine.speak("This is a long message that should be interrupted. " * 5)
    await asyncio.sleep(1)
    await tts_engine.speak("Interrupting with this message!", interrupt=True)
    await asyncio.sleep(3)
    
    # Stop the engine
    print("Stopping Edge TTS engine...")
    await tts_engine.stop()
    print("Test complete")

if __name__ == "__main__":
    # Run the test
    asyncio.run(main()) 