#!/usr/bin/env python3
"""
JARVIS Web Speech Connector

This module serves a web interface for speech recognition and handles
communication between the browser-based speech recognition and JARVIS.
"""

import os
import sys
import json
import logging
import threading
import asyncio
from pathlib import Path
from typing import Callable, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JarvisWebSpeech")

# Add project root to the path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Try to import required libraries
try:
    from flask import Flask, render_template, request, jsonify, send_from_directory
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    logger.warning("Flask not found. Install with: pip install flask flask-cors")
    FLASK_AVAILABLE = False

class WebSpeechConnector:
    """
    Web Speech API connector for JARVIS that provides a web interface
    for speech recognition using the browser's capabilities.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the web speech connector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.active = False
        self.server_thread = None
        
        # Default settings
        self.settings = {
            "host": self.config.get("host", "127.0.0.1"),
            "port": self.config.get("port", 5000),
            "debug": self.config.get("debug", False),
            "html_path": self.config.get("html_path", os.path.join(project_root, "src", "web")),
            "wake_word": self.config.get("wake_word", "jarvis")
        }
        
        # Command processor callback
        self.command_processor = None
        
        # Last received command
        self.last_command = None
        
        # Setup Flask app
        if FLASK_AVAILABLE:
            self.app = Flask(__name__, 
                             static_folder=self.settings["html_path"],
                             template_folder=self.settings["html_path"])
            CORS(self.app)
            
            # Register routes
            self.register_routes()
        else:
            self.app = None
            logger.error("Cannot initialize web speech connector - Flask not available")
    
    def register_routes(self):
        """Register Flask routes."""
        
        @self.app.route('/')
        def index():
            """Serve the main speech recognition page."""
            try:
                return send_from_directory(self.settings["html_path"], "speech_recognition.html")
            except Exception as e:
                logger.error(f"Error serving speech_recognition.html: {e}")
                return f"Error: {str(e)}", 500
        
        @self.app.route('/api/command', methods=['POST'])
        def receive_command():
            """Receive a command from the web interface."""
            try:
                data = request.json
                command = data.get('command', '')
                
                if not command:
                    return jsonify({"status": "error", "message": "No command provided"}), 400
                
                logger.info(f"Received command from web interface: {command}")
                self.last_command = command
                
                # Process the command if a processor is registered
                response = {"status": "received", "command": command}
                
                if self.command_processor:
                    try:
                        # Process command in a separate thread to avoid blocking
                        threading.Thread(target=self.command_processor, args=(command,)).start()
                        response["status"] = "processing"
                    except Exception as e:
                        logger.error(f"Error processing command: {e}")
                        response["status"] = "error"
                        response["message"] = str(e)
                else:
                    logger.warning("Command received but no processor is registered")
                    response["status"] = "no_processor"
                
                return jsonify(response)
            
            except Exception as e:
                logger.error(f"Error processing command request: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/status')
        def get_status():
            """Get the status of the web speech connector."""
            return jsonify({
                "active": self.active,
                "wake_word": self.settings["wake_word"],
                "last_command": self.last_command
            })
        
        @self.app.route('/api/settings', methods=['GET', 'POST'])
        def handle_settings():
            """Get or update settings."""
            if request.method == 'GET':
                return jsonify({
                    "wake_word": self.settings["wake_word"]
                })
            
            elif request.method == 'POST':
                try:
                    data = request.json
                    
                    # Update wake word if provided
                    if 'wake_word' in data:
                        self.settings["wake_word"] = data["wake_word"]
                        logger.info(f"Wake word updated to: {self.settings['wake_word']}")
                    
                    return jsonify({"status": "success", "settings": {
                        "wake_word": self.settings["wake_word"]
                    }})
                
                except Exception as e:
                    logger.error(f"Error updating settings: {e}")
                    return jsonify({"status": "error", "message": str(e)}), 500
    
    def start(self, command_processor: Callable[[str], None] = None):
        """
        Start the web speech connector.
        
        Args:
            command_processor: Function to process voice commands
            
        Returns:
            bool: True if started successfully, False otherwise
        """
        if not FLASK_AVAILABLE:
            logger.error("Cannot start web speech connector - Flask not available")
            return False
        
        if self.active:
            logger.warning("Web speech connector already running")
            return True
        
        self.command_processor = command_processor
        
        try:
            # Start Flask server in a separate thread
            self.server_thread = threading.Thread(
                target=self.app.run,
                kwargs={
                    'host': self.settings["host"],
                    'port': self.settings["port"],
                    'debug': self.settings["debug"],
                    'use_reloader': False
                }
            )
            self.server_thread.daemon = True
            self.server_thread.start()
            
            self.active = True
            logger.info(f"Web speech connector started at http://{self.settings['host']}:{self.settings['port']}")
            
            # Provide instructions
            logger.info("Open the URL in a browser to use web-based speech recognition")
            
            return True
        
        except Exception as e:
            logger.error(f"Error starting web speech connector: {e}")
            return False
    
    def stop(self):
        """
        Stop the web speech connector.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.active:
            return True
            
        try:
            # Flask doesn't have a clean shutdown method when running in a thread
            # We'll mark it as inactive, but the actual server will continue running
            # until the process exits
            self.active = False
            logger.info("Web speech connector marked as inactive")
            
            return True
        
        except Exception as e:
            logger.error(f"Error stopping web speech connector: {e}")
            return False
    
    def set_wake_word(self, wake_word):
        """
        Set the wake word.
        
        Args:
            wake_word: Wake word to use
        """
        self.settings["wake_word"] = wake_word
        logger.info(f"Wake word set to: {wake_word}")


# Standalone function to run the web speech connector
def run_web_speech(host="127.0.0.1", port=5000):
    """
    Run the web speech connector as a standalone application.
    
    Args:
        host: Host address to bind
        port: Port to use
    """
    # Simple command processor for testing
    def process_command(cmd):
        print(f"Command received: {cmd}")
        print("In a real environment, this would be processed by JARVIS")
    
    # Create and start the connector
    connector = WebSpeechConnector({
        "host": host,
        "port": port,
        "debug": True
    })
    
    started = connector.start(process_command)
    
    if started:
        print(f"Web speech connector started at http://{host}:{port}")
        print("Open this URL in a browser to use web-based speech recognition")
        print("Press Ctrl+C to exit")
        
        try:
            # Keep the main thread alive
            while connector.active:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping web speech connector...")
        finally:
            connector.stop()
            print("Web speech connector stopped")
    else:
        print("Failed to start web speech connector")


# For testing
if __name__ == "__main__":
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description="JARVIS Web Speech Connector")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="Port to use (default: 5000)")
    
    args = parser.parse_args()
    
    run_web_speech(args.host, args.port) 