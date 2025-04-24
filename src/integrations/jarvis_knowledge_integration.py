#!/usr/bin/env python3
"""
JARVIS Knowledge Base Integration Module

This module integrates the knowledge base with voice recognition and voice engine components,
allowing JARVIS to respond to knowledge-related queries.
"""

import sys
import re
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

# Add project root to the path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JarvisKnowledgeIntegration")

# Import JARVIS components
try:
    from src.tools.knowledge_base import KnowledgeBase
    from src.tools.voice_recognition import SpeechRecognition
    
    # Try to import voice engine if available
    try:
        from src.tools.voice_engine import VoiceEngine
        VOICE_ENGINE_AVAILABLE = True
    except ImportError:
        logger.warning("Voice engine not available. Text-to-speech will be disabled.")
        VOICE_ENGINE_AVAILABLE = False
    
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Error importing JARVIS components: {e}")
    COMPONENTS_AVAILABLE = False

class KnowledgeIntegration:
    """
    Integrates knowledge base with voice recognition and synthesis.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the knowledge integration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.is_running = False
        
        # Initialize components
        if COMPONENTS_AVAILABLE:
            self.kb = KnowledgeBase()
            self.speech = SpeechRecognition()
            
            if VOICE_ENGINE_AVAILABLE:
                self.voice = VoiceEngine()
            else:
                self.voice = None
                
            logger.info("Knowledge integration initialized successfully")
        else:
            logger.error("Knowledge integration initialization failed due to missing components")
            self.kb = None
            self.speech = None
            self.voice = None
    
    def start(self):
        """Start the knowledge integration."""
        if not COMPONENTS_AVAILABLE:
            logger.error("Cannot start knowledge integration - components not available")
            return False
            
        if self.is_running:
            logger.warning("Knowledge integration already running")
            return True
            
        # Start voice recognition
        if self.speech:
            self.speech.start(self._process_command)
            
        # Start voice engine
        if self.voice:
            self.voice.start()
            
        self.is_running = True
        logger.info("Knowledge integration started")
        return True
    
    def stop(self):
        """Stop the knowledge integration."""
        if not self.is_running:
            logger.warning("Knowledge integration not running")
            return True
            
        # Stop voice recognition
        if self.speech:
            self.speech.stop()
            
        # Stop voice engine
        if self.voice:
            self.voice.stop()
            
        self.is_running = False
        logger.info("Knowledge integration stopped")
        return True
    
    def _process_command(self, command: str):
        """
        Process a voice command.
        
        Args:
            command: The voice command to process
        """
        logger.info(f"Processing command: {command}")
        
        # Handle knowledge-related commands
        if any(pattern in command.lower() for pattern in [
            "tell me about", "what is", "who is", "what are", "search for",
            "find information", "look up", "information on"
        ]):
            self._handle_knowledge_query(command)
        elif "remember" in command.lower() or "store" in command.lower() or "save" in command.lower():
            self._handle_knowledge_storage(command)
        else:
            # Not a knowledge-related command
            if self.voice:
                self.voice.speak("I'm not sure how to help with that.")
            logger.info("Command not recognized as a knowledge query")
    
    def _handle_knowledge_query(self, command: str):
        """
        Handle a knowledge query command.
        
        Args:
            command: The query command
        """
        # Extract the search query from the command
        query = None
        
        # Different patterns to extract queries
        patterns = [
            r"tell me about (.+)",
            r"what is (?:a |an )?(.+)",
            r"who is (.+)",
            r"what are (.+)",
            r"search for (.+)",
            r"find information (?:on |about )?(.+)",
            r"look up (.+)",
            r"information on (.+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command.lower())
            if match:
                query = match.group(1).strip()
                break
        
        if not query:
            if self.voice:
                self.voice.speak("I'm not sure what you're asking about.")
            return
            
        logger.info(f"Searching knowledge base for: {query}")
        
        # Search the knowledge base
        results = self.kb.search(query)
        
        if not results:
            if self.voice:
                self.voice.speak(f"I don't have any information about {query}.")
            else:
                print(f"No information found about {query}.")
            return
            
        # Get the most relevant result
        result = results[0]
        
        # Prepare the response
        if 'type' in result and result['type'] == 'text' and 'content' in result:
            response = result['content']
            title = result.get('title', 'this topic')
            
            # Truncate very long responses
            if len(response) > 300:
                response = response[:300] + "..."
                
            if self.voice:
                self.voice.speak(f"Here's what I know about {title}. {response}")
            else:
                print(f"Information about {title}:")
                print(response)
        else:
            # Handle structured data
            if 'name' in result:
                name = result['name']
                description = result.get('description', 'No description available')
                
                if self.voice:
                    self.voice.speak(f"Here's information about {name}. {description}")
                else:
                    print(f"Information about {name}:")
                    print(description)
                    
                # Additional details for different types
                if 'type' in result:
                    type_name = result['type']
                    if type_name == 'system' and 'capabilities' in result:
                        capabilities = ", ".join(result['capabilities'][:3])
                        if self.voice:
                            self.voice.speak(f"{name} has capabilities including: {capabilities}")
                        else:
                            print(f"Capabilities: {capabilities}")
                    elif type_name == 'person' and 'theories' in result:
                        theories = ", ".join(result['theories'])
                        if self.voice:
                            self.voice.speak(f"{name} is known for: {theories}")
                        else:
                            print(f"Known for: {theories}")
            else:
                # Generic handling
                if self.voice:
                    self.voice.speak(f"I found information related to {query}, but I don't know how to present it.")
                else:
                    print(f"Found information about {query}, but it's in a format I can't explain.")
    
    def _handle_knowledge_storage(self, command: str):
        """
        Handle a command to store information.
        
        Args:
            command: The storage command
        """
        # Extract the information to store
        match = re.search(r"(?:remember|store|save)(?: that)? (.+)", command.lower())
        
        if not match:
            if self.voice:
                self.voice.speak("I'm not sure what you want me to remember.")
            return
            
        info = match.group(1).strip()
        
        # Detect category if mentioned
        category = "personal"
        for cat in ["general", "science", "technology"]:
            if f"in {cat}" in command.lower() or f"under {cat}" in command.lower():
                category = cat
                # Remove the category specification from the info
                info = re.sub(f"(?:in|under) {cat}", "", info).strip()
                
        # Generate a title based on the first few words
        words = info.split()
        title = " ".join(words[:min(5, len(words))])
        
        # Store the information
        path = self.kb.store_text(info, title, category)
        
        if self.voice:
            self.voice.speak(f"I'll remember that {info}")
        logger.info(f"Stored information: '{info}' with title '{title}' in category '{category}'")


# For testing
if __name__ == "__main__":
    print("Initializing JARVIS Knowledge Integration...")
    
    integration = KnowledgeIntegration()
    
    if not integration.kb or not integration.speech:
        print("Knowledge integration initialization failed. Exiting.")
        sys.exit(1)
    
    # Add some test knowledge if the knowledge base is empty
    if not integration.kb.list_entries():
        print("Knowledge base is empty. Adding sample data...")
        
        # Add a basic entry about JARVIS
        integration.kb.store_text(
            "JARVIS is an AI assistant inspired by the fictional system in the Marvel Universe. "
            "It can process voice commands, search for information, and assist with various tasks.",
            "About JARVIS",
            "general"
        )
        
        # Add some scientific information
        integration.kb.store_text(
            "The solar system consists of the Sun and everything that orbits around it, "
            "including planets, dwarf planets, moons, asteroids, comets, and meteoroids.",
            "Solar System",
            "science"
        )
        
        print("Sample data added.")
    
    # Test processing some commands directly
    test_commands = [
        "Tell me about JARVIS",
        "What is the solar system",
        "Remember that my favorite color is blue",
        "Search for information on artificial intelligence"
    ]
    
    print("\nTesting command processing:")
    
    for command in test_commands:
        print(f"\nProcessing: '{command}'")
        integration._process_command(command)
        time.sleep(1)  # Give time for voice to complete
    
    # If you want to test with actual voice recognition, uncomment this:
    """
    print("\nStarting knowledge integration with voice recognition...")
    integration.start()
    
    try:
        # Keep the script running
        print("Say something like 'Jarvis, tell me about the solar system'")
        print("Press Ctrl+C to exit")
        while integration.is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping knowledge integration...")
        integration.stop()
    """
    
    print("\nKnowledge integration test complete.") 