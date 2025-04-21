import requests
import json
import os
import threading
import time

class JARVISVoiceConnector:
    """
    Helper class to connect the GUI voice button with the enhanced JARVIS server
    """
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url
        self.voice_enabled = True
        self.voice_provider = "gtts"  # Default to the more natural voice
        self.check_server_status()
    
    def check_server_status(self):
        """Check if the JARVIS server is running and get current voice status"""
        try:
            response = requests.get(f"{self.server_url}/jarvis://voice_status", timeout=2)
            if response.status_code == 200:
                data = response.json()
                self.voice_enabled = data.get("enabled", True)
                self.voice_provider = data.get("provider", "gtts")
                return True
            return False
        except Exception:
            return False
    
    def toggle_voice(self):
        """Toggle voice on/off"""
        try:
            response = requests.post(f"{self.server_url}/toggle_voice", timeout=2)
            if response.status_code == 200:
                data = response.json()
                self.voice_enabled = data.get("voice_enabled", True)
                return self.voice_enabled
            return None
        except Exception:
            return None
    
    def change_voice_provider(self, provider="gtts"):
        """Change voice provider between gtts and pyttsx3"""
        try:
            response = requests.post(
                f"{self.server_url}/change_voice",
                json={"provider": provider},
                timeout=2
            )
            if response.status_code == 200:
                data = response.json()
                self.voice_provider = data.get("voice_provider", provider)
                return True
            return False
        except Exception:
            return False
    
    def speak(self, text):
        """Send text to be spoken by JARVIS"""
        if not text or not self.voice_enabled:
            return False
        
        try:
            response = requests.post(
                f"{self.server_url}/",
                json={"method": "generate_voice", "params": {"text": text}},
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

# Simple test function
def test_voice_connector():
    connector = JARVISVoiceConnector()
    
    if connector.check_server_status():
        print(f"Connected to JARVIS. Voice enabled: {connector.voice_enabled}")
        
        # Test speaking
        connector.speak("JARVIS voice system is now connected to the GUI.")
        time.sleep(3)
        
        # Test toggling voice
        new_state = connector.toggle_voice()
        print(f"Voice toggled to: {new_state}")
        time.sleep(1)
        
        # Turn voice back on
        if not new_state:
            connector.toggle_voice()
            
        # Test changing voice provider
        current = connector.voice_provider
        new_provider = "pyttsx3" if current == "gtts" else "gtts"
        
        print(f"Changing voice from {current} to {new_provider}")
        connector.change_voice_provider(new_provider)
        
        connector.speak("Voice provider has been changed. How does this sound?")
    else:
        print("Could not connect to JARVIS server")

if __name__ == "__main__":
    test_voice_connector() 