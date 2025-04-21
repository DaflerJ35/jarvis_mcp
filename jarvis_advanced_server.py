from enhanced_jarvis_server import app, generate_voice, process_text_command
from jarvis_system_control import JARVISSystemControl
from jarvis_voice_recognition import JARVISVoiceRecognition
import threading
import time
import queue
import uvicorn
from fastapi import FastAPI, BackgroundTasks, Request, Response
import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Initialize the main components
system_control = JARVISSystemControl()
voice_recognition = None  # Will initialize when needed to avoid blocking startup

# Command processing queue
command_queue = queue.Queue()

# Status tracking
voice_rec_active = False
last_voice_command = ""
last_system_action = ""
startup_time = datetime.now()

# JARVIS Advanced Server - combines all capabilities
class JARVISAdvancedServer:
    """
    Advanced JARVIS server that combines voice recognition, system control,
    and voice output to create a movie-like experience
    """
    def __init__(self):
        self.running = False
        self.processing_thread = None
        self.system_control = system_control
        self.voice_recognition = None
        
    def start(self):
        """Start the advanced server components"""
        if self.running:
            return False
            
        self.running = True
        
        # Start the command processing thread
        self.processing_thread = threading.Thread(target=self._process_commands)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        # Delayed start of voice recognition to avoid blocking startup
        def delayed_voice_rec_init():
            time.sleep(2)  # Wait for server to fully start
            global voice_recognition
            try:
                print("Initializing voice recognition...")
                voice_recognition = JARVISVoiceRecognition(wake_word="jarvis")
                voice_recognition.start_listening(continuous=True)
                global voice_rec_active
                voice_rec_active = True
                print("Voice recognition started")
                generate_voice("JARVIS is now online and listening for commands.")
            except Exception as e:
                print(f"Error initializing voice recognition: {e}")
        
        # Start voice recognition in a separate thread
        threading.Thread(target=delayed_voice_rec_init).daemon = True
        threading.Thread(target=delayed_voice_rec_init).start()
        
        return True
        
    def stop(self):
        """Stop the advanced server components"""
        self.running = False
        
        # Stop voice recognition if active
        global voice_recognition, voice_rec_active
        if voice_recognition and voice_rec_active:
            voice_recognition.stop_listening()
            voice_rec_active = False
        
        if self.processing_thread:
            self.processing_thread.join(timeout=1)
            self.processing_thread = None
            
        return True
    
    def _process_commands(self):
        """Background thread to process commands from voice and API"""
        global last_voice_command, last_system_action, voice_recognition
        
        print("Command processing started")
        
        while self.running:
            # Check for voice commands if voice recognition is active
            if voice_recognition and voice_rec_active:
                voice_command = voice_recognition.get_next_command(block=False)
                if voice_command:
                    source, text = voice_command
                    if source == "VOICE":
                        last_voice_command = text
                        print(f"Processing voice command: {text}")
                        
                        # Process the system command
                        response = self.system_control.process_system_command(text)
                        last_system_action = response
                        
                        # Generate voice response
                        generate_voice(response)
                    elif source == "SYSTEM" and text == "wake_word_detected":
                        # Say hello when activated
                        generate_voice("Yes, I'm listening.")
            
            # Check for API commands in the queue
            try:
                api_command = command_queue.get(block=False)
                print(f"Processing API command: {api_command}")
                
                # Process the command
                if "command" in api_command:
                    cmd_text = api_command["command"]
                    response = self.system_control.process_system_command(cmd_text)
                    last_system_action = response
                    
                    # Generate voice if requested
                    if api_command.get("voice_response", True):
                        generate_voice(response)
                    
                    # Store the result if callback provided
                    if "callback_queue" in api_command:
                        api_command["callback_queue"].put(response)
            except queue.Empty:
                pass
            
            # Sleep to prevent busy-waiting
            time.sleep(0.1)
            
    def process_command(self, command_text, voice_response=True):
        """Process a command from the API and optionally generate voice response"""
        print(f"Received API command: {command_text}")
        
        # Create a response queue
        response_queue = queue.Queue()
        
        # Put the command in the queue
        command_queue.put({
            "command": command_text,
            "voice_response": voice_response,
            "callback_queue": response_queue
        })
        
        # Wait for the response with timeout
        try:
            response = response_queue.get(timeout=5)
            return response
        except queue.Empty:
            return "Command processing timed out"

# Create the advanced server instance
advanced_server = JARVISAdvancedServer()

# Add API endpoints for the advanced functionality
@app.get("/jarvis://status")
async def get_status():
    """Get the status of the advanced JARVIS system"""
    uptime = datetime.now() - startup_time
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return {
        "status": "online",
        "uptime": f"{hours}h {minutes}m {seconds}s",
        "voice_recognition_active": voice_rec_active,
        "last_voice_command": last_voice_command,
        "last_system_action": last_system_action,
        "features": [
            "voice_recognition",
            "system_control",
            "voice_output"
        ]
    }

@app.post("/execute")
async def execute_command(request: Request):
    """Execute a system command and return the result"""
    try:
        data = await request.json()
        command = data.get("command", "")
        voice_response = data.get("voice_response", True)
        
        if not command:
            return {"error": "No command provided"}
        
        result = advanced_server.process_command(command, voice_response)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

@app.post("/start_voice_recognition")
async def start_voice_recognition():
    """Start voice recognition if not already active"""
    global voice_recognition, voice_rec_active
    
    if voice_rec_active:
        return {"status": "already_active"}
    
    try:
        if not voice_recognition:
            voice_recognition = JARVISVoiceRecognition(wake_word="jarvis")
        
        voice_recognition.start_listening(continuous=True)
        voice_rec_active = True
        return {"status": "started"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/stop_voice_recognition")
async def stop_voice_recognition():
    """Stop voice recognition if active"""
    global voice_recognition, voice_rec_active
    
    if not voice_rec_active:
        return {"status": "not_active"}
    
    try:
        if voice_recognition:
            voice_recognition.stop_listening()
        
        voice_rec_active = False
        return {"status": "stopped"}
    except Exception as e:
        return {"error": str(e)}

@app.on_event("startup")
async def startup_event():
    """Initialize the advanced server on startup"""
    print("Starting JARVIS Advanced Server...")
    advanced_server.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup when shutting down"""
    print("Shutting down JARVIS Advanced Server...")
    advanced_server.stop()

# Run the server if executed as a script
if __name__ == "__main__":
    port = int(os.environ.get("JARVIS_PORT", 8000))
    print(f"Starting JARVIS Advanced Server on port {port}")
    print("This version has full movie-like capabilities:")
    print("1. Voice control with wake word 'Jarvis'")
    print("2. System control (open apps, search web, etc.)")
    print("3. Natural voice output")
    uvicorn.run(app, host="0.0.0.0", port=port) 