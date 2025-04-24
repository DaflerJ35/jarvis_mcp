#!/usr/bin/env python3
"""
Test Script for Improved JARVIS Voice Interactions

This script demonstrates the improved JARVIS voice interactions using
the enhanced voice components and web-based speech recognition.
"""

import os
import sys
import time
import asyncio
import argparse
import threading
from pathlib import Path

# Add project root to the path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Import JARVIS components
from src.tools.enhanced_voice import EnhancedVoice
from src.web.web_speech_connector import WebSpeechConnector

# Try to import Edge TTS Engine (optional)
try:
    from src.tools.edge_tts_engine import EdgeTTSEngine
    EDGE_TTS_AVAILABLE = True
except ImportError:
    print("Edge TTS Engine not available. Using standard voice engine.")
    EDGE_TTS_AVAILABLE = False

# Try to import knowledge base (optional)
try:
    from src.tools.knowledge_base import KnowledgeBase
    KB_AVAILABLE = True
except ImportError:
    print("Knowledge Base not available. Some features will be limited.")
    KB_AVAILABLE = False

# Try to import multimodal processor (optional)
try:
    from jarvis_modules.multimodal import MultiModalProcessor
    MM_AVAILABLE = True
except ImportError:
    print("Multimodal processor not available. Some features will be limited.")
    MM_AVAILABLE = False

# Try to import autonomous evolution system (optional)
try:
    from jarvis_modules.autonomous_evolution import CodeEvolutionSystem
    EVOLUTION_AVAILABLE = True
except ImportError:
    print("Autonomous Evolution System not available. Some features will be limited.")
    EVOLUTION_AVAILABLE = False

class ImprovedJarvisDemo:
    """Demo class for the improved JARVIS voice interactions."""
    
    def __init__(self, config=None):
        """Initialize the demo."""
        self.config = config or {}
        self.running = False
        
        # Initialize components
        self.voice_system = None
        self.edge_tts = None
        self.web_speech = None
        self.knowledge_base = None
        self.multimodal = None
        self.evolution = None
        
        # Command handlers
        self.command_handlers = {
            "hello": self._handle_hello,
            "what time": self._handle_time,
            "tell me about": self._handle_info,
            "who are you": self._handle_who,
            "what can you do": self._handle_capabilities,
            "stop": self._handle_stop,
            "exit": self._handle_stop,
            "quit": self._handle_stop,
            "sleep": self._handle_sleep,
            "wake up": self._handle_wake,
            "help": self._handle_help,
            "switch voice": self._handle_switch_voice,
            "web interface": self._handle_web_interface
        }
        
        # State
        self.sleeping = False
        
        # Stats
        self.command_count = 0
        self.start_time = None
    
    async def initialize(self):
        """Initialize all components."""
        print("Initializing JARVIS components...")
        
        # Initialize voice system
        self.voice_system = EnhancedVoice(self.config.get("voice", {}))
        
        # Initialize Edge TTS if available
        if EDGE_TTS_AVAILABLE:
            self.edge_tts = EdgeTTSEngine(self.config.get("edge_tts", {}))
            await self.edge_tts.start()
        
        # Initialize knowledge base if available
        if KB_AVAILABLE:
            self.knowledge_base = KnowledgeBase()
            
            # Add some basic knowledge if empty
            if not self.knowledge_base.list_entries():
                self.knowledge_base.store_text(
                    "JARVIS is an AI assistant inspired by the fictional system in the Marvel Universe. "
                    "It can process voice commands, search for information, and assist with various tasks.",
                    "About JARVIS",
                    "general"
                )
        
        # Initialize multimodal processor if available
        if MM_AVAILABLE and self.knowledge_base:
            self.multimodal = MultiModalProcessor(self.knowledge_base)
            await self.multimodal.start()
        
        # Initialize evolution system if available
        if EVOLUTION_AVAILABLE and self.knowledge_base:
            class MockCodingBridge:
                async def generate_code(self, prompt, language):
                    return {"code": "# This is a mock implementation\ndef hello():\n    print('Hello world')"}
            
            self.evolution = CodeEvolutionSystem(MockCodingBridge(), self.knowledge_base)
            await self.evolution.start()
        
        # Start web speech connector in a separate thread
        if self.config.get("use_web_speech", True):
            self.web_speech = WebSpeechConnector(self.config.get("web_speech", {}))
            self.web_speech.start(self.process_command)
        
        # Start voice system
        await self.voice_system.start(self.process_command)
        
        self.running = True
        self.start_time = time.time()
        
        print("JARVIS initialization complete.")
        return True
    
    async def shutdown(self):
        """Shut down all components."""
        print("Shutting down JARVIS...")
        self.running = False
        
        # Stop voice system
        if self.voice_system:
            self.voice_system.stop()
        
        # Stop Edge TTS
        if self.edge_tts:
            await self.edge_tts.stop()
        
        # Stop web speech connector
        if self.web_speech:
            self.web_speech.stop()
        
        # Stop multimodal processor
        if self.multimodal:
            await self.multimodal.shutdown()
        
        # Stop evolution system
        if self.evolution:
            await self.evolution.shutdown()
        
        print("JARVIS shutdown complete.")
        return True
    
    def process_command(self, command):
        """Process a voice command."""
        if not self.running:
            return
        
        # Increment command count
        self.command_count += 1
        
        # Check if sleeping
        if self.sleeping and not any(wake_cmd in command.lower() for wake_cmd in ["wake up", "wake", "hey jarvis"]):
            # Only respond to wake up commands when sleeping
            return
        
        # Reset sleeping state if wake command received
        if self.sleeping and any(wake_cmd in command.lower() for wake_cmd in ["wake up", "wake", "hey jarvis"]):
            self.sleeping = False
        
        # Find matching handler
        handler = None
        for key, func in self.command_handlers.items():
            if key in command.lower():
                handler = func
                break
        
        if handler:
            # Execute the handler
            handler(command)
        else:
            # Default response
            self._default_response(command)
    
    def _handle_hello(self, command):
        """Handle hello command."""
        self.voice_system.speak("Hello! How can I assist you today?")
    
    def _handle_time(self, command):
        """Handle time query."""
        import datetime
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        self.voice_system.speak(f"The current time is {current_time}")
    
    def _handle_info(self, command):
        """Handle information request."""
        # Extract the topic
        topic = command.lower().split("tell me about")[1].strip()
        
        if not topic:
            self.voice_system.speak("What would you like to know about?")
            return
        
        # Check knowledge base if available
        if self.knowledge_base:
            results = self.knowledge_base.search(topic)
            
            if results:
                # Get the most relevant result
                result = results[0]
                
                if 'type' in result and result['type'] == 'text' and 'content' in result:
                    response = result['content']
                    title = result.get('title', topic)
                    
                    self.voice_system.speak(f"Here's what I know about {title}: {response}")
                    return
            
            # If no results or not in the right format
            self.voice_system.speak(f"I don't have specific information about {topic} in my knowledge base. Would you like me to search for it?")
        else:
            self.voice_system.speak(f"I don't have access to the knowledge base to look up information about {topic}.")
    
    def _handle_who(self, command):
        """Handle identity question."""
        self.voice_system.speak(
            "I am JARVIS, Just A Rather Very Intelligent System. "
            "I'm designed to assist with a wide range of tasks through voice commands and natural language interaction. "
            "My capabilities include controlling your computer, searching for information, and providing assistance with various tasks."
        )
    
    def _handle_capabilities(self, command):
        """Handle capabilities question."""
        self.voice_system.speak(
            "I can perform various tasks including answering questions, controlling your computer, "
            "searching for information, and providing assistance with various daily activities. "
            "Just ask me what you need help with, and I'll do my best to assist you."
        )
    
    def _handle_stop(self, command):
        """Handle stop command."""
        self.voice_system.speak("Shutting down JARVIS. Goodbye!")
        
        # Schedule shutdown
        threading.Thread(target=lambda: asyncio.run(self.shutdown())).start()
    
    def _handle_sleep(self, command):
        """Handle sleep command."""
        self.sleeping = True
        self.voice_system.speak("Entering sleep mode. Say 'wake up' to reactivate me.")
    
    def _handle_wake(self, command):
        """Handle wake command."""
        if self.sleeping:
            self.sleeping = False
            self.voice_system.speak("I'm awake and ready to assist you.")
        else:
            self.voice_system.speak("I'm already awake and listening.")
    
    def _handle_help(self, command):
        """Handle help command."""
        self.voice_system.speak(
            "Here are some commands you can try: "
            "Ask me what time it is, tell me about a topic, ask who I am, "
            "or what I can do. You can also ask me to sleep or wake up."
        )
    
    def _handle_switch_voice(self, command):
        """Handle voice switching command."""
        if EDGE_TTS_AVAILABLE and self.edge_tts:
            # Use Edge TTS for this response
            asyncio.create_task(self.edge_tts.speak("Switching to Microsoft Edge TTS voice. How does this sound?"))
        else:
            self.voice_system.speak("I don't have additional voice options available.")
    
    def _handle_web_interface(self, command):
        """Handle web interface command."""
        if self.web_speech:
            host = self.web_speech.settings["host"]
            port = self.web_speech.settings["port"]
            self.voice_system.speak(
                f"The web interface is available at http://{host}:{port}. "
                "Open this URL in your browser to use web-based speech recognition."
            )
        else:
            self.voice_system.speak("The web interface is not currently active.")
    
    def _default_response(self, command):
        """Handle unrecognized commands."""
        self.voice_system.speak(f"I heard: {command}, but I'm not sure how to respond to that. Try asking for help if you need assistance.")
    
    def get_status(self):
        """Get the status of the demo."""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        status = {
            "running": self.running,
            "sleeping": self.sleeping,
            "uptime_seconds": uptime,
            "command_count": self.command_count,
            "components": {
                "voice_system": self.voice_system is not None,
                "edge_tts": self.edge_tts is not None,
                "web_speech": self.web_speech is not None,
                "knowledge_base": self.knowledge_base is not None,
                "multimodal": self.multimodal is not None,
                "evolution": self.evolution is not None
            }
        }
        
        return status


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Improved JARVIS Voice Interactions Demo")
    parser.add_argument("--no-web", action="store_true", help="Disable web interface")
    parser.add_argument("--host", default="127.0.0.1", help="Web interface host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Web interface port (default: 5000)")
    
    args = parser.parse_args()
    
    # Configure JARVIS
    config = {
        "use_web_speech": not args.no_web,
        "web_speech": {
            "host": args.host,
            "port": args.port
        },
        "voice": {
            "wake_word": "jarvis",
            "use_conversational_responses": True
        }
    }
    
    # Create and initialize JARVIS
    jarvis = ImprovedJarvisDemo(config)
    await jarvis.initialize()
    
    if jarvis.running:
        print("\nJARVIS is now running.")
        print("Talk to JARVIS or type 'exit' to quit.")
        
        if jarvis.web_speech:
            host = jarvis.web_speech.settings["host"]
            port = jarvis.web_speech.settings["port"]
            print(f"Web interface available at: http://{host}:{port}")
        
        # Main interaction loop
        try:
            while jarvis.running:
                # Accept text input as an alternative to voice
                user_input = input("> ")
                
                if user_input.lower() in ["exit", "quit", "stop"]:
                    await jarvis.shutdown()
                    break
                
                # Process the text command
                jarvis.process_command(user_input)
                
                # Small delay to avoid tight loop
                await asyncio.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
        
        except Exception as e:
            print(f"Error in main loop: {e}")
        
        finally:
            # Ensure proper shutdown
            if jarvis.running:
                await jarvis.shutdown()
    
    print("JARVIS demo complete.")


if __name__ == "__main__":
    asyncio.run(main()) 