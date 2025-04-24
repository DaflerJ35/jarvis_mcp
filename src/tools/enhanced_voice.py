#!/usr/bin/env python3
"""
JARVIS Enhanced Voice Integration Module

This module provides an improved voice interaction experience combining
speech recognition and text-to-speech with more natural responses.
"""

import os
import sys
import time
import random
import logging
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JarvisEnhancedVoice")

# Add project root to the path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

try:
    # Import voice components
    from src.tools.voice_recognition import SpeechRecognition
    from src.tools.voice_engine import VoiceEngine
    
    VOICE_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Error importing voice components: {e}")
    VOICE_COMPONENTS_AVAILABLE = False

class EnhancedVoice:
    """
    Enhanced voice interaction system that provides a more natural and
    responsive speech experience for JARVIS.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the enhanced voice system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.is_running = False
        
        # Default settings
        self.settings = {
            "wake_word": self.config.get("wake_word", "jarvis"),
            "voice_provider": self.config.get("voice_provider", "pyttsx3"),
            "voice_id": self.config.get("voice_id", None),
            "speaking_rate": self.config.get("speaking_rate", 175),
            "volume": self.config.get("volume", 1.0),
            "continuous_listening": self.config.get("continuous_listening", True),
            "use_conversational_responses": self.config.get("use_conversational_responses", True),
            "audio_cues": self.config.get("audio_cues", True)
        }
        
        # Init voice components
        if VOICE_COMPONENTS_AVAILABLE:
            self.recognition = SpeechRecognition({
                "wake_word": self.settings["wake_word"],
                "energy_threshold": self.config.get("energy_threshold", 4000),
                "pause_threshold": self.config.get("pause_threshold", 0.8),
                "dynamic_energy_threshold": self.config.get("dynamic_energy_threshold", True)
            })
            
            self.voice = VoiceEngine(provider=self.settings["voice_provider"])
            
            # Set voice properties
            if self.settings["voice_id"]:
                self.voice.set_voice(self.settings["voice_id"])
            
            self.voice.set_rate(self.settings["speaking_rate"])
            self.voice.set_volume(self.settings["volume"])
            
            logger.info("Enhanced voice system initialized successfully")
        else:
            self.recognition = None
            self.voice = None
            logger.error("Cannot initialize enhanced voice system - components not available")
        
        # Commands processor
        self.command_processor = None
        
        # Setup response variations for more natural interactions
        self._setup_response_variations()
        
        # State tracking
        self.last_interaction_time = 0
        self.total_interactions = 0
        self.successful_commands = 0
        
        # Background processing flag
        self.processing = False
    
    def _setup_response_variations(self):
        """Setup response variations for more natural conversation."""
        self.acknowledgments = [
            "I'm on it",
            "Working on that",
            "Processing your request",
            "Right away",
            "Consider it done"
        ]
        
        self.confirmations = [
            "Done",
            "Complete",
            "Task finished",
            "All set",
            "Completed successfully"
        ]
        
        self.greetings = [
            "Hello, how can I help?",
            "Hi there",
            "At your service",
            "Greetings"
        ]
        
        self.continuation_phrases = [
            "The rest of the result has been printed to the chat screen, kindly check it out",
            "The rest of the text is now on the chat screen, please check it",
            "You can see the rest of the text on the chat screen",
            "The remaining part of the text is now on the chat screen",
            "You'll find more text on the chat screen for you to see",
            "The rest of the answer is now on the chat screen"
        ]
        
        self.thinking_phrases = [
            "Processing that",
            "Let me think about that",
            "Analyzing your request",
            "Working on it",
            "Computing"
        ]
        
        self.error_phrases = [
            "I encountered an issue with that request",
            "Sorry, I couldn't complete that task",
            "There was a problem processing your request",
            "I ran into a difficulty with that",
            "I wasn't able to do that"
        ]
    
    async def start(self, command_processor: Callable[[str], None] = None):
        """
        Start the enhanced voice system.
        
        Args:
            command_processor: Function to process voice commands
            
        Returns:
            bool: True if started successfully, False otherwise
        """
        if not VOICE_COMPONENTS_AVAILABLE:
            logger.error("Cannot start enhanced voice system - components not available")
            return False
        
        if self.is_running:
            logger.warning("Enhanced voice system is already running")
            return True
        
        self.command_processor = command_processor
        
        try:
            # Start voice engine
            engine_started = self.voice.start()
            if not engine_started:
                logger.error("Failed to start voice engine")
                return False
            
            # Start speech recognition with our command handler
            recognition_started = self.recognition.start(self._handle_command)
            if not recognition_started:
                logger.error("Failed to start speech recognition")
                self.voice.stop()
                return False
            
            self.is_running = True
            
            # Play startup sound if audio cues enabled
            if self.settings["audio_cues"]:
                # Simulate startup sound
                pass
            
            # Welcome message
            welcome = random.choice(self.greetings)
            self.voice.speak(welcome)
            
            logger.info("Enhanced voice system started successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error starting enhanced voice system: {e}")
            return False
    
    def stop(self):
        """
        Stop the enhanced voice system.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.is_running:
            logger.warning("Enhanced voice system is not running")
            return True
        
        try:
            # Stop components
            if self.recognition:
                self.recognition.stop()
            
            if self.voice:
                self.voice.stop()
            
            self.is_running = False
            logger.info("Enhanced voice system stopped")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping enhanced voice system: {e}")
            return False
    
    def _handle_command(self, command: str):
        """
        Handle a voice command internally.
        
        Args:
            command: The voice command to process
        """
        # Update interaction stats
        self.last_interaction_time = time.time()
        self.total_interactions += 1
        
        # Log the command
        logger.info(f"Processing command: {command}")
        
        # Provide audio/voice feedback
        if not self.processing:
            # Indicate we're processing
            if self.settings["use_conversational_responses"]:
                ack = random.choice(self.acknowledgments)
                self.voice.speak(ack)
            
            # Set processing flag to avoid interrupting the response
            self.processing = True
            
            # Process in a separate thread to avoid blocking
            threading.Thread(target=self._process_command_thread, args=(command,)).start()
        else:
            # We're already processing something, notify user
            self.voice.speak("I'm still working on your previous request")
    
    def _process_command_thread(self, command):
        """Process a command in a separate thread."""
        try:
            # Forward to the main command processor if available
            if self.command_processor:
                self.command_processor(command)
                self.successful_commands += 1
            else:
                # Simple echo if no processor
                time.sleep(0.5)  # Simulate processing
                response = f"I heard: {command}, but I don't have a command processor configured"
                self.voice.speak(response)
        
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            # Notify user of error
            error_msg = random.choice(self.error_phrases)
            self.voice.speak(f"{error_msg}: {str(e)}")
        
        finally:
            # Clear processing flag
            self.processing = False
    
    def speak(self, text, interrupt=False):
        """
        Speak text aloud.
        
        Args:
            text: Text to speak
            interrupt: Whether to interrupt current speech
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_running or not self.voice:
            logger.warning("Cannot speak - voice system is not running")
            return False
        
        try:
            # If text is too long, speak concisely and offer to show details
            if len(text) > 300:
                summary = text[:250] + "..."
                continuation = random.choice(self.continuation_phrases)
                
                # Speak the summary
                self.voice.speak(summary)
                time.sleep(0.3)
                
                # Let the user know the rest is on screen
                self.voice.speak(continuation)
                return True
            else:
                # Just speak the text
                return self.voice.speak(text, interrupt)
        
        except Exception as e:
            logger.error(f"Error speaking text: {e}")
            return False
    
    def thinking(self):
        """
        Indicate that JARVIS is thinking/processing.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_running or not self.voice:
            return False
        
        try:
            thinking_phrase = random.choice(self.thinking_phrases)
            return self.voice.speak(thinking_phrase)
        
        except Exception as e:
            logger.error(f"Error in thinking indicator: {e}")
            return False
    
    def confirm(self, success=True):
        """
        Speak a confirmation message.
        
        Args:
            success: Whether the operation was successful
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_running or not self.voice:
            return False
        
        try:
            if success:
                message = random.choice(self.confirmations)
            else:
                message = random.choice(self.error_phrases)
            
            return self.voice.speak(message)
        
        except Exception as e:
            logger.error(f"Error in confirmation: {e}")
            return False
    
    def is_available(self):
        """
        Check if the enhanced voice system is available.
        
        Returns:
            bool: True if available, False otherwise
        """
        return (VOICE_COMPONENTS_AVAILABLE and 
                self.recognition is not None and 
                self.voice is not None and
                self.recognition.is_available())
    
    def get_status(self):
        """
        Get the current status of the enhanced voice system.
        
        Returns:
            dict: Status information
        """
        status = {
            "available": self.is_available(),
            "running": self.is_running,
            "wake_word": self.settings["wake_word"],
            "voice_provider": self.settings["voice_provider"],
            "interactions": {
                "total": self.total_interactions,
                "successful": self.successful_commands,
                "last_interaction": self.last_interaction_time
            }
        }
        
        if self.recognition:
            recognition_diagnostics = self.recognition.get_diagnostics()
            status["recognition"] = recognition_diagnostics
        
        return status


# For testing
if __name__ == "__main__":
    print("Testing Enhanced Voice System")
    
    # Simple command processor for testing
    def process_command(cmd):
        print(f"Command received: {cmd}")
        if "hello" in cmd.lower():
            time.sleep(0.5)  # Simulate processing
            voice_system.speak("Hello to you too!")
        elif "time" in cmd.lower():
            import datetime
            current_time = datetime.datetime.now().strftime("%H:%M")
            voice_system.speak(f"The current time is {current_time}")
        elif "weather" in cmd.lower():
            voice_system.speak("I'm sorry, I don't have access to weather data in this test")
        elif "long text" in cmd.lower():
            long_text = "This is a very long response that would normally be truncated. " * 10
            voice_system.speak(long_text)
        else:
            voice_system.speak(f"I heard your command: {cmd}")
    
    # Create and start the voice system
    voice_system = EnhancedVoice()
    
    if not voice_system.is_available():
        print("Enhanced voice system is not available. Please check your configuration and dependencies.")
        sys.exit(1)
    
    # Start the voice system with our test processor
    import asyncio
    asyncio.run(voice_system.start(process_command))
    
    try:
        print(f"Enhanced voice system is running. Say '{voice_system.settings['wake_word']} <command>' to test")
        print("Press Ctrl+C to exit")
        
        # Keep the main thread alive
        while voice_system.is_running:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nStopping enhanced voice system...")
    
    finally:
        voice_system.stop()
        print("Enhanced voice system stopped.") 