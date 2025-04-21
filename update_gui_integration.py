import sys
import os
import threading
import time
import subprocess

def run_jarvis_system():
    """Run the complete JARVIS system - server and GUI with voice integration"""
    print("Starting the JARVIS Enhanced System...")
    
    # First kill any existing Python processes to free the port
    try:
        os.system("taskkill /F /IM python.exe")
        os.system("taskkill /F /IM pythonw.exe")
        time.sleep(2)  # Wait for processes to terminate
    except:
        pass
    
    # Start the enhanced server in a background process
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Wait for server to initialize
    print("Waiting for server to initialize...")
    time.sleep(5)
    
    # Start the GUI
    start_gui()

def start_server():
    """Start the enhanced JARVIS server"""
    try:
        subprocess.run(["python", "enhanced_jarvis_server.py"], shell=True)
    except Exception as e:
        print(f"Error starting server: {str(e)}")

def start_gui():
    """Start the JARVIS GUI"""
    try:
        subprocess.run(["python", "jarvis_gui.py"], shell=True)
    except Exception as e:
        print(f"Error starting GUI: {str(e)}")

def check_dependencies():
    """Check for all required dependencies"""
    required_packages = [
        "fastapi", "uvicorn", "pydantic", "pyttsx3", "gtts", 
        "playsound", "PyQt5", "PyQtWebEngine", "requests"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"Installing missing packages: {', '.join(missing)}")
        os.system(f"pip install {' '.join(missing)}")
    
    return True

if __name__ == "__main__":
    # Check dependencies
    check_dependencies()
    
    # Run the system
    run_jarvis_system() 