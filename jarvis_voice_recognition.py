import speech_recognition as sr
import threading
import time
import queue
import os
import json
import pyaudio
import wave
import tempfile
import numpy as np
from datetime import datetime
import logging
import sounddevice as sd
from pydub import AudioSegment
from pydub.playback import play
import re
import winsound

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('JARVISVoiceRecognition')

class JARVISVoiceRecognition:
    """
    Voice recognition module for JARVIS that allows it to listen for voice commands
    like in the movies - with wake word detection and continuous listening
    """
    def __init__(self, command_callback=None, sound_feedback=True, 
                 wake_words=None, default_mode="seamless",
                 logger=None, sensitivity=1.0):
        """
        Initialize the JARVIS voice recognition system.
        
        Args:
            command_callback: Function to call when a command is recognized
            sound_feedback: Whether to play sound feedback
            wake_words: List of wake words to activate voice recognition
            default_mode: Default listening mode (single, wake_word, seamless)
            logger: Logger to use
            sensitivity: Microphone sensitivity multiplier
        """
        # Setup voice recognition
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()
        self.command_callback = command_callback or (lambda x: print(f"Command: {x}"))
        self.sound_feedback = sound_feedback
        self.command_queue = queue.Queue()
        
        # Default wake words if none provided
        self.wake_words = wake_words or ["jarvis", "hey jarvis", "okay jarvis", "hey j"]
        
        # Set up logger
        self.logger = logger or logging.getLogger("JARVIS_Voice")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Voice recognition state
        self.running = False
        self.paused = False
        self.listening_thread = None
        self.processing_thread = None
        
        # Listening mode
        # - single: Listen for a single command then stop
        # - wake_word: Listen continuously but only process commands after wake word
        # - seamless: Process all speech as commands
        self.mode = default_mode
        
        # Sensitivity adjustment (for microphone)
        self.sensitivity = sensitivity
        
        # Last detection time for debouncing wake word detection
        self.last_wake_word_time = 0
        self.wake_word_cooldown = 1.0  # seconds
        
        # Exit commands
        self.exit_commands = ["exit", "quit", "stop listening", "go to sleep"]
        
        # Setup paths
        self.setup_paths()
        
        # Adjust recognizer settings for better accuracy
        self.calibrate_microphone()
        
        # Setup logging
        self.logger.info("Voice recognition system initialized")
    
    def setup_paths(self):
        """Setup paths for voice recognition"""
        # Implementation of setup_paths method
        pass

    def load_custom_commands(self):
        """Load custom voice commands from file"""
        try:
            with open('config/voice_commands.json', 'r') as f:
                return json.load(f)
        except:
            return {}

    def play_activation_sound(self):
        """Play a sound to indicate voice activation"""
        try:
            sound_file = self.config.get('activation_sound', 'sounds/activation.wav')
            if os.path.exists(sound_file):
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                winsound.Beep(1000, 200)  # Fallback beep
        except:
            pass  # Sound is optional

    def play_deactivation_sound(self):
        """Play a sound to indicate voice deactivation"""
        try:
            sound_file = self.config.get('deactivation_sound', 'sounds/deactivation.wav')
            if os.path.exists(sound_file):
                winsound.PlaySound(sound_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                winsound.Beep(500, 200)  # Fallback beep
        except:
            pass  # Sound is optional

    def start_listening(self, continuous=False, seamless=False):
        """Start listening for voice commands
        
        Args:
            continuous: If True, continuously listen for commands
            seamless: If True, process all speech without wake word
        """
        if self.running:
            return
            
        self.running = True
        self.paused = False
        
        # Log the mode
        mode_type = "seamless" if seamless else ("continuous with wake word" if continuous else "single command")
        self.logger.info(f"Starting voice recognition in {mode_type} mode")
        
        # Start listening in a separate thread
        self.listening_thread = threading.Thread(target=self._listen_thread, daemon=True)
        self.listening_thread.start()
        
        # Play activation sound
        self.play_activation_sound()

    def stop_listening(self):
        """Stop listening for voice commands"""
        if not self.running:
            return
            
        self.logger.info("Stopping voice recognition")
        self.running = False
        self.paused = True
        
        if self.listening_thread and self.listening_thread.is_alive():
            self.listening_thread.join(timeout=1.0)
            
        # Play deactivation sound
        self.play_deactivation_sound()

    def _listen_thread(self):
        """Background thread for listening to voice"""
        try:
            if self.mode == "seamless":
                self.listen_continuously_seamless()
            elif self.mode == "wake_word":
                self._continuous_listen()
            else:
                self._single_listen()
        except Exception as e:
            self.logger.error(f"Error in listening thread: {str(e)}")
            self.running = False

    def _single_listen(self):
        """Listen for a single command"""
        try:
            with self.mic as source:
                self.logger.info("Listening for a single command...")
                audio = self.recognizer.listen(source, timeout=5.0, phrase_time_limit=10.0)
                
            text = self.recognizer.recognize_google(audio)
            self.logger.info(f"Recognized: {text}")
            self.command_queue.put(text.lower())
            
        except sr.WaitTimeoutError:
            self.logger.info("No speech detected within timeout")
        except sr.UnknownValueError:
            self.logger.info("Could not understand audio")
        except sr.RequestError as e:
            self.logger.error(f"Recognition error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error in single listen: {str(e)}")
            
        # Single listen mode automatically stops after one command
        self.running = False

    def _continuous_listen(self):
        """Continuously listen for commands"""
        self.logger.info(f"Continuous listening started in {'seamless' if self.mode == 'seamless' else 'wake word'} mode")
        
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            # Main listening loop
            while self.running and not self.paused:
                try:
                    self.logger.debug("Listening for speech...")
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=10.0)
                    
                    try:
                        text = self.recognizer.recognize_google(audio).lower()
                        self.logger.info(f"Recognized: {text}")
                        
                        if self.mode == "seamless":
                            # In seamless mode, all speech is processed
                            if any(cmd in text for cmd in self.exit_commands):
                                self.logger.info("Exit command detected")
                                break
                            else:
                                self.command_queue.put(text)
                                # Give visual feedback that command was received
                                self.play_activation_sound()
                        else:
                            # In wake word mode, check for wake word
                            if any(phrase in text for phrase in self.wake_words):
                                # Wake word detected, play activation sound
                                self.play_activation_sound()
                                self.logger.info("Wake word detected, listening for command")
                                
                                # Listen for the actual command
                                follow_up_audio = self.recognizer.listen(source, timeout=5.0, phrase_time_limit=10.0)
                                follow_up_text = self.recognizer.recognize_google(follow_up_audio).lower()
                                self.logger.info(f"Command after wake word: {follow_up_text}")
                                
                                # Process the command
                                if any(cmd in follow_up_text for cmd in self.exit_commands):
                                    self.logger.info("Exit command detected")
                                    break
                                else:
                                    self.command_queue.put(follow_up_text)
                    
                    except sr.UnknownValueError:
                        self.logger.debug("Could not understand audio")
                    except sr.RequestError as e:
                        self.logger.error(f"Recognition error: {str(e)}")
                        time.sleep(1)  # Wait before trying again
                
                except Exception as e:
                    self.logger.error(f"Error in continuous listen: {str(e)}")
                    time.sleep(1)  # Wait before trying again
        
        self.running = False
        self.logger.info("Continuous listening stopped")

    def calibrate_microphone(self):
        """Calibrate the microphone for ambient noise"""
        try:
            with self.mic as source:
                self.logger.info("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Apply sensitivity adjustment
                self.recognizer.energy_threshold = int(300 * self.sensitivity)  # Default is 300
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.6  # Reduced from 0.8 for more responsive experience
                self.recognizer.phrase_threshold = 0.3  # Lower threshold for detecting speech
                
                self.logger.info(f"Microphone calibrated. Energy threshold: {self.recognizer.energy_threshold}")
        except Exception as e:
            self.logger.error(f"Error calibrating microphone: {str(e)}")

    def listen_continuously_seamless(self):
        """Listen continuously and process all speech as commands in seamless mode."""
        self.logger.info("Starting seamless listening mode")
        
        # Configuration for seamless listening
        active_phrase_timeout = 1.0  # Reduced from 1.5 to make commands process faster
        energy_threshold_adjust_rate = 30  # Reduced frequency of ambient noise adjustment
        ambient_adjust_duration = 0.3  # Shorter duration for quick adjustments
        
        # Enhanced initial calibration
        self.calibrate_microphone()
        
        loop_count = 0
        last_phrase_time = 0
        current_command = ""
        ongoing_conversation = False
        
        while self.running and not self.paused:
            try:
                # Periodic ambient noise adjustment (less frequent)
                if loop_count % energy_threshold_adjust_rate == 0:
                    with self.mic as source:
                        self.logger.debug("Quick ambient noise adjustment...")
                        self.recognizer.adjust_for_ambient_noise(source, duration=ambient_adjust_duration)
                
                loop_count += 1
                
                # Listen for speech with appropriate timeout based on conversation state
                with self.mic as source:
                    self.logger.debug("Listening in seamless mode...")
                    if ongoing_conversation:
                        # During active conversation, use shorter phrase time limit for more natural back-and-forth
                        audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=7)
                    else:
                        # When waiting for new commands, use longer phrase time limit
                        audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=15)
                
                # Convert speech to text
                text = self.recognizer.recognize_google(audio).lower()
                current_time = time.time()
                
                if text:
                    self.logger.info(f"Recognized in seamless mode: {text}")
                    
                    # Check for exit commands
                    if any(cmd in text for cmd in self.exit_commands):
                        self.logger.info("Exit command detected")
                        self.command_queue.put("exit voice recognition")
                        break
                    
                    # If this is part of an ongoing command (within timeout)
                    if current_time - last_phrase_time < active_phrase_timeout and current_command:
                        current_command += " " + text
                        self.logger.debug(f"Adding to current command: {current_command}")
                        ongoing_conversation = True
                    else:
                        # This is a new command
                        if current_command:
                            # Process the previous command if there was one
                            self.logger.info(f"Processing complete command: {current_command}")
                            self.command_callback(current_command)
                        
                        # Start a new command
                        current_command = text
                        ongoing_conversation = True
                    
                    # Update the last phrase time
                    last_phrase_time = current_time
                    
                    # Play a subtle sound feedback to indicate successful voice capture
                    if self.sound_feedback:
                        self.play_activation_sound()
                
                # Check if there's been a significant pause, indicating command completion
                elif current_time - last_phrase_time > active_phrase_timeout and current_command:
                    self.logger.info(f"Processing completed command after pause: {current_command}")
                    self.command_callback(current_command)
                    current_command = ""
                    ongoing_conversation = False
                
            except sr.WaitTimeoutError:
                # No speech detected, check if we need to submit the current command
                current_time = time.time()
                if current_time - last_phrase_time > active_phrase_timeout and current_command:
                    self.logger.info(f"Processing completed command after timeout: {current_command}")
                    self.command_callback(current_command)
                    current_command = ""
                    ongoing_conversation = False
                    
            except sr.UnknownValueError:
                # Speech was unintelligible
                self.logger.debug("Could not understand audio in seamless mode")
                
                # Still update the conversation state
                current_time = time.time()
                if current_time - last_phrase_time > active_phrase_timeout * 2:
                    ongoing_conversation = False
                    if current_command:
                        self.logger.info(f"Processing final command after unintelligible speech: {current_command}")
                        self.command_callback(current_command)
                        current_command = ""
                
            except Exception as e:
                self.logger.error(f"Error in seamless listening: {str(e)}")
                time.sleep(0.5)  # Prevent tight loop if persistent errors
                
                # Reset conversation state if error
                if current_time - last_phrase_time > active_phrase_timeout and current_command:
                    self.logger.info(f"Processing command before error recovery: {current_command}")
                    self.command_callback(current_command)
                    current_command = ""
                    ongoing_conversation = False

    def get_next_command(self, block=False, timeout=None):
        """Get the next command from the queue
        
        Args:
            block: If True, block until a command is available
            timeout: Timeout in seconds for blocking
            
        Returns:
            Command string or None if no command is available
        """
        try:
            return self.command_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    def is_running(self):
        """Check if voice recognition is active"""
        return self.running
        
    def is_seamless_mode(self):
        """Check if in seamless mode"""
        return self.mode == "seamless"
    
    def has_pending_commands(self):
        """Check if there are pending commands in the queue"""
        return not self.command_queue.empty()

# Simple test function
def test_voice_recognition():
    """Test the voice recognition functionality"""
    voice_rec = JARVISVoiceRecognition(wake_words=["jarvis"])
    
    print("Starting voice recognition test...")
    print("Say 'Jarvis' to activate, then speak a command")
    print("Say 'go to sleep' to put JARVIS back to sleep")
    print("Say 'shut down' to exit the test")
    
    voice_rec.start_listening(continuous=True)
    
    try:
        while True:
            command = voice_rec.get_next_command(block=True, timeout=1)
            if command:
                source, text = command
                
                if source == "SYSTEM":
                    if text == "wake_word_detected":
                        print("🎙️ JARVIS is now listening for your command...")
                    elif text == "sleep_mode_activated":
                        print("💤 JARVIS is now sleeping")
                    elif text == "shutdown_requested":
                        print("🛑 Shutting down voice recognition")
                        break
                elif source == "VOICE":
                    print(f"Command received: {text}")
                    print("Processing command...")
                    # Here you would connect to the system control module
                    # For this test, we just echo the command
            
            # Small pause to prevent CPU overuse
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("Test interrupted by user")
    finally:
        voice_rec.stop_listening()
        print("Voice recognition test completed")

if __name__ == "__main__":
    test_voice_recognition() 