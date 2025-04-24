#!/usr/bin/env python3
"""
JARVIS Voice Recognition Diagnostic Tool

This script helps diagnose issues with the JARVIS voice recognition system by:
1. Checking if all required dependencies are installed
2. Testing microphone access and listing available devices
3. Verifying speech recognition functionality
4. Providing detailed error messages and installation guidance
5. Offering interactive testing of voice recognition
"""

import os
import sys
import time
import logging
import json
import platform
import argparse
from pathlib import Path
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JarvisVoiceDiagnostics")

# Define required dependencies
REQUIRED_MODULES = {
    "speech_recognition": {
        "import_name": "speech_recognition",
        "package_name": "SpeechRecognition",
        "install_cmd": "pip install SpeechRecognition"
    },
    "pyaudio": {
        "import_name": "pyaudio",
        "package_name": "PyAudio",
        "install_cmd": {
            "Windows": "pip install pipwin && pipwin install pyaudio",
            "Linux": "pip install pyaudio (may require sudo apt-get install portaudio19-dev)",
            "Darwin": "pip install pyaudio (may require brew install portaudio)"
        }
    },
    "pocketsphinx": {
        "import_name": "pocketsphinx",
        "package_name": "PocketSphinx",
        "install_cmd": "pip install pocketsphinx",
        "optional": True
    }
}

def check_module(module_info):
    """Check if a Python module is installed and return its status."""
    try:
        if importlib.util.find_spec(module_info["import_name"]):
            # Try to actually import it to catch any loading errors
            importlib.import_module(module_info["import_name"])
            return True
        return False
    except ImportError:
        return False
    except Exception as e:
        logger.error(f"Error loading {module_info['package_name']}: {e}")
        return False

def check_environment():
    """Check Python version and OS information."""
    env_info = {
        "python_version": platform.python_version(),
        "os_name": platform.system(),
        "os_version": platform.release(),
        "platform": platform.platform()
    }
    
    if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 6):
        logger.warning("JARVIS requires Python 3.6 or higher")
        env_info["python_compatible"] = False
    else:
        env_info["python_compatible"] = True
        
    return env_info

def check_jarvis_modules():
    """Check if JARVIS voice recognition module is available."""
    try:
        jarvis_path = Path(__file__).parent
        src_tools_path = jarvis_path / "src" / "tools"
        
        if not src_tools_path.exists():
            # Try looking up one level
            src_tools_path = jarvis_path.parent / "src" / "tools"
            
        voice_rec_path = src_tools_path / "voice_recognition.py"
        
        result = {
            "jarvis_found": False,
            "voice_recognition_found": False,
            "path_checked": str(voice_rec_path)
        }
        
        if voice_rec_path.exists():
            result["voice_recognition_found"] = True
            # Add to path to make it importable
            sys.path.append(str(src_tools_path.parent))
            result["jarvis_found"] = True
            
        return result
    except Exception as e:
        logger.error(f"Error checking JARVIS modules: {e}")
        return {
            "jarvis_found": False,
            "voice_recognition_found": False,
            "error": str(e)
        }

def check_microphones():
    """Check available microphones and test access."""
    if not check_module(REQUIRED_MODULES["speech_recognition"]) or not check_module(REQUIRED_MODULES["pyaudio"]):
        return {
            "available": False,
            "error": "Required dependencies missing (SpeechRecognition or PyAudio)",
            "devices": []
        }
        
    try:
        import speech_recognition as sr
        
        mic_list = sr.Microphone.list_microphone_names()
        
        result = {
            "available": len(mic_list) > 0,
            "devices": mic_list,
            "count": len(mic_list)
        }
        
        # Test microphone access by attempting to capture audio
        if result["available"]:
            try:
                with sr.Microphone() as source:
                    recognizer = sr.Recognizer()
                    logger.info("Testing microphone access...")
                    # Just a quick test to see if we can access the mic
                    recognizer.adjust_for_ambient_noise(source, duration=1)
                    result["access_test"] = "successful"
            except Exception as e:
                result["access_test"] = "failed"
                result["access_error"] = str(e)
                
        return result
    except Exception as e:
        logger.error(f"Error checking microphones: {e}")
        return {
            "available": False,
            "error": str(e),
            "devices": []
        }

def test_jarvis_recognition():
    """Test JARVIS voice recognition module."""
    try:
        # Try to import the JARVIS voice recognition module
        jarvis_modules = check_jarvis_modules()
        
        if not jarvis_modules["voice_recognition_found"]:
            return {
                "available": False,
                "error": "JARVIS voice recognition module not found"
            }
            
        # Import the module
        try:
            from src.tools.voice_recognition import SpeechRecognition
            
            # Create an instance and get diagnostics
            speech = SpeechRecognition()
            diagnostics = speech.get_diagnostics()
            
            result = {
                "available": speech.is_available(),
                "diagnostics": diagnostics
            }
            
            return result
        except Exception as e:
            logger.error(f"Error importing JARVIS voice recognition module: {e}")
            return {
                "available": False,
                "error": str(e)
            }
    except Exception as e:
        logger.error(f"Error testing JARVIS recognition: {e}")
        return {
            "available": False,
            "error": str(e)
        }

def run_interactive_test(mic_device=None, wake_word="jarvis", continuous=False):
    """Run an interactive test of the voice recognition system.
    
    Args:
        mic_device: Optional index of microphone device to use
        wake_word: Wake word to use (default: "jarvis")
        continuous: Whether to run in continuous mode listening for commands
    """
    try:
        # Import the JARVIS voice recognition module
        from src.tools.voice_recognition import SpeechRecognition
        
        # Create configuration
        config = {
            "wake_word": wake_word,
            "energy_threshold": 4000,  # Adjust based on environment
            "pause_threshold": 0.8
        }
        
        print(f"\n{'='*20} INTERACTIVE VOICE TEST {'='*20}")
        print(f"Wake word: '{wake_word}'")
        
        # Create speech recognition instance
        speech = SpeechRecognition(config)
        
        if not speech.is_available():
            print("❌ Speech recognition is not available. Please check previous diagnostics.")
            return False
            
        print("✅ Speech recognition is available.")
        
        if continuous:
            # Define callback for continuous mode
            def command_callback(command):
                print(f"Command recognized: '{command}'")
                if command.lower() in ["exit", "quit", "stop"]:
                    speech.stop()
            
            print(f"\nStarting continuous recognition mode.")
            print(f"Say '{wake_word} <command>' to test.")
            print(f"Say '{wake_word} exit' to quit.")
            
            # Start continuous recognition
            speech.start(command_callback)
            
            try:
                # Keep the main thread alive
                while speech.is_running:
                    time.sleep(0.5)
            except KeyboardInterrupt:
                print("\nInterrupted by user.")
            finally:
                speech.stop()
                print("Voice recognition test stopped.")
        else:
            # Single recognition test
            try:
                print("\nPlease speak something in 3 seconds...")
                time.sleep(3)
                
                print("Listening...")
                text = speech.listen_once(timeout=7)
                
                if text:
                    print(f"\nRecognized: '{text}'")
                    
                    # Check if wake word was in the text
                    if wake_word.lower() in text.lower():
                        print(f"✅ Wake word '{wake_word}' detected!")
                    else:
                        print(f"❌ Wake word '{wake_word}' not detected.")
                else:
                    print("\n❌ No speech recognized or there was an error.")
            except Exception as e:
                print(f"\n❌ Error during recognition: {e}")
        
        return True
    except Exception as e:
        print(f"\n❌ Error in interactive test: {e}")
        return False

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="JARVIS Voice Recognition Diagnostic Tool")
    parser.add_argument("--interactive", "-i", action="store_true", 
                        help="Run interactive voice recognition test")
    parser.add_argument("--continuous", "-c", action="store_true",
                        help="Run continuous voice recognition test")
    parser.add_argument("--wake-word", "-w", type=str, default="jarvis",
                        help="Wake word to use in interactive test (default: 'jarvis')")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose logging")
    
    return parser.parse_args()

def main():
    """Run diagnostic checks and display results."""
    # Parse command-line arguments
    args = parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("\n" + "="*80)
    print(" "*30 + "JARVIS VOICE DIAGNOSTICS")
    print("="*80 + "\n")
    
    # Check environment
    print("Checking environment...")
    env_info = check_environment()
    print(f"Python version: {env_info['python_version']} ({'Compatible' if env_info['python_compatible'] else 'Not compatible - Python 3.6+ required'})")
    print(f"Operating system: {env_info['os_name']} {env_info['os_version']}\n")
    
    # Check dependencies
    print("Checking required dependencies...")
    dependencies_ok = True
    for module_name, module_info in REQUIRED_MODULES.items():
        is_installed = check_module(module_info)
        status = "✓" if is_installed else "✗"
        optional_text = " (optional)" if module_info.get("optional", False) else ""
        print(f"  {status} {module_info['package_name']}{optional_text}")
        
        if not is_installed and not module_info.get("optional", False):
            dependencies_ok = False
            
            # Get platform-specific install command if available
            if isinstance(module_info["install_cmd"], dict):
                install_cmd = module_info["install_cmd"].get(
                    env_info["os_name"], 
                    module_info["install_cmd"].get("default", "pip install " + module_info["package_name"])
                )
            else:
                install_cmd = module_info["install_cmd"]
                
            print(f"    Installation: {install_cmd}")
    
    print("")
    
    # Check JARVIS modules
    print("Checking JARVIS installation...")
    jarvis_modules = check_jarvis_modules()
    if jarvis_modules["voice_recognition_found"]:
        print(f"  ✓ JARVIS voice recognition module found")
    else:
        print(f"  ✗ JARVIS voice recognition module not found")
        print(f"    Checked: {jarvis_modules['path_checked']}")
    print("")
    
    # Only proceed with further checks if dependencies are available
    mic_info = {"available": False}
    jarvis_test = {"available": False}
    
    if dependencies_ok:
        # Check microphones
        print("Checking microphone devices...")
        mic_info = check_microphones()
        
        if mic_info["available"]:
            print(f"  ✓ Found {mic_info['count']} microphone devices:")
            for i, device in enumerate(mic_info["devices"]):
                print(f"    {i}: {device}")
                
            if mic_info.get("access_test", "") == "successful":
                print("  ✓ Microphone access test successful")
            else:
                print(f"  ✗ Microphone access test failed: {mic_info.get('access_error', 'Unknown error')}")
        else:
            print(f"  ✗ No microphone devices available")
            if "error" in mic_info:
                print(f"    Error: {mic_info['error']}")
        print("")
        
        # Test JARVIS voice recognition
        if jarvis_modules["voice_recognition_found"]:
            print("Testing JARVIS voice recognition...")
            jarvis_test = test_jarvis_recognition()
            
            if jarvis_test["available"]:
                print("  ✓ JARVIS voice recognition is operational")
                
                # Print additional diagnostic information
                diagnostics = jarvis_test.get("diagnostics", {})
                if "recognizer" in diagnostics:
                    print("  Recognition settings:")
                    for key, value in diagnostics["recognizer"].items():
                        print(f"    {key}: {value}")
            else:
                print(f"  ✗ JARVIS voice recognition is not operational")
                if "error" in jarvis_test:
                    print(f"    Error: {jarvis_test['error']}")
            print("")
    
    # Summary
    print("-"*80)
    print("DIAGNOSTIC SUMMARY:")
    
    if not env_info["python_compatible"]:
        print("❌ Python version not compatible. Please install Python 3.6 or higher.")
    
    if not dependencies_ok:
        print("❌ Required dependencies missing. Please install them using the commands above.")
    
    if not jarvis_modules["voice_recognition_found"]:
        print("❌ JARVIS voice recognition module not found. Please check your installation.")
    
    if dependencies_ok and "available" in mic_info and not mic_info["available"]:
        print("❌ No microphones detected. Please check your microphone connection.")
    
    if dependencies_ok and jarvis_modules["voice_recognition_found"] and jarvis_test["available"] == False:
        print("❌ JARVIS voice recognition is not operational. See errors above.")
        
    all_tests_passed = (env_info["python_compatible"] and 
                        dependencies_ok and 
                        jarvis_modules["voice_recognition_found"] and 
                        mic_info["available"] and 
                        jarvis_test["available"])
                        
    if all_tests_passed:
        print("✅ All diagnostics passed! Your JARVIS voice recognition system should be working correctly.")
    else:
        print("\nSome issues were found. Please fix them to ensure proper operation of JARVIS voice recognition.")
    
    print("-"*80)
    
    # Run interactive test if requested and all tests passed
    if args.interactive and all_tests_passed:
        print("\nStarting interactive voice recognition test...")
        run_interactive_test(wake_word=args.wake_word, continuous=args.continuous)
    elif args.interactive and not all_tests_passed:
        print("\n❌ Cannot run interactive test due to diagnostics failures.")
        print("   Please fix the issues above before running the interactive test.")
    
    if not args.interactive and all_tests_passed:
        print("\nRun with --interactive (-i) flag to test voice recognition.")
        print("Example: python diagnose_voice.py --interactive")
        print("For continuous recognition: python diagnose_voice.py --interactive --continuous")

if __name__ == "__main__":
    main() 