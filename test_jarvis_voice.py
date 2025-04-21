import requests
import json
import os
import sys
import time

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'

# Configuration
JARVIS_URL = "http://localhost:8000"
TEST_TEXT = "Hello, I am JARVIS, your personal assistant. Voice synthesis is now working correctly."

def print_color(text, color):
    """Print colored text to the terminal"""
    print(f"{color}{text}{Colors.ENDC}")

def check_server_status():
    """Check if the JARVIS server is running"""
    print_color("Checking JARVIS server status...", Colors.BLUE)
    try:
        response = requests.get(JARVIS_URL, timeout=5)
        if response.status_code == 200:
            print_color("✓ JARVIS server is running", Colors.GREEN)
            return True
        else:
            print_color(f"✗ JARVIS server returned status code {response.status_code}", Colors.RED)
            return False
    except requests.exceptions.RequestException as e:
        print_color(f"✗ JARVIS server is not running: {str(e)}", Colors.RED)
        return False

def test_voice_generation():
    """Test voice generation functionality"""
    print_color("\nTesting voice generation...", Colors.BLUE)
    try:
        response = requests.post(
            f"{JARVIS_URL}/",
            json={"method": "generate_voice", "params": {"text": TEST_TEXT}},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "audio_path" in data or "audio_data" in data:
                print_color("✓ Voice generation successful!", Colors.GREEN)
                print_color(f"Response: {json.dumps(data, indent=2)}", Colors.GREEN)
                return True
            else:
                print_color("✗ Voice generation failed - no audio data returned", Colors.RED)
                print_color(f"Response: {json.dumps(data, indent=2)}", Colors.YELLOW)
                return False
        else:
            print_color(f"✗ Voice generation failed with status code {response.status_code}", Colors.RED)
            print_color(f"Response: {response.text}", Colors.YELLOW)
            return False
    except requests.exceptions.RequestException as e:
        print_color(f"✗ Error connecting to JARVIS: {str(e)}", Colors.RED)
        return False

def check_dependencies():
    """Check if voice dependencies are installed"""
    print_color("\nChecking voice dependencies...", Colors.BLUE)
    
    try:
        # Try to import common voice-related packages
        import importlib
        
        voice_packages = ["pyttsx3", "gtts", "playsound"]
        missing_packages = []
        
        for package in voice_packages:
            try:
                importlib.import_module(package)
                print_color(f"✓ {package} is installed", Colors.GREEN)
            except ImportError:
                missing_packages.append(package)
                print_color(f"✗ {package} is NOT installed", Colors.RED)
        
        if missing_packages:
            print_color("\nMissing voice dependencies. Installing them now...", Colors.YELLOW)
            os.system(f"pip install {' '.join(missing_packages)}")
            print_color("Dependency installation complete. Please run this test again.", Colors.GREEN)
            return False
        
        return True
    except Exception as e:
        print_color(f"✗ Error checking dependencies: {str(e)}", Colors.RED)
        return False

def install_voice_packages():
    """Install all required voice packages"""
    print_color("\nInstalling voice packages...", Colors.BLUE)
    
    packages = [
        "pyttsx3",      # Offline TTS
        "gtts",         # Google TTS
        "playsound",    # Audio playback
        "pydub",        # Audio processing
        "SpeechRecognition"  # For voice recognition
    ]
    
    try:
        os.system(f"pip install {' '.join(packages)}")
        print_color("Voice packages installed successfully", Colors.GREEN)
        return True
    except Exception as e:
        print_color(f"✗ Error installing voice packages: {str(e)}", Colors.RED)
        return False

def fix_jarvis_voice():
    """Attempt to fix JARVIS voice capabilities"""
    print_color("\nAttempting to fix JARVIS voice capabilities...", Colors.BLUE)
    
    # Install missing dependencies
    install_voice_packages()
    
    # Update .env file to ensure voice is enabled
    try:
        with open('.env', 'r') as f:
            env_content = f.read()
        
        if 'ENABLE_VOICE' not in env_content:
            with open('.env', 'a') as f:
                f.write("\n# Voice configuration\nENABLE_VOICE=true\nVOICE_PROVIDER=pyttsx3\n")
        
        print_color("✓ .env file updated with voice settings", Colors.GREEN)
    except Exception as e:
        print_color(f"✗ Error updating .env file: {str(e)}", Colors.RED)
    
    print_color("\nFix completed. Please restart JARVIS and test again.", Colors.GREEN)

def main():
    """Main function to run the voice test"""
    print_color("=== JARVIS VOICE TEST ===", Colors.BLUE)
    
    # Step 1: Check if server is running
    if not check_server_status():
        print_color("\nPlease start the JARVIS server first (run jarvis_launcher.bat)", Colors.YELLOW)
        sys.exit(1)
    
    # Step 2: Check voice dependencies
    deps_ok = check_dependencies()
    
    # Step 3: Test voice generation
    voice_ok = test_voice_generation()
    
    # If issues found, try to fix them
    if not voice_ok:
        should_fix = input("\nWould you like to attempt to fix voice capabilities? (y/n): ").lower()
        if should_fix == 'y':
            fix_jarvis_voice()
    else:
        print_color("\nVoice test completed successfully!", Colors.GREEN)

if __name__ == "__main__":
    main() 