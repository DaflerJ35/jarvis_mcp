import sys
import os
import importlib
import subprocess
import platform

print("===== JARVIS VOICE DIAGNOSTIC TOOL =====")
print(f"Running on {platform.system()} {platform.release()}")

# Check if required packages are installed
print("\n1. Checking voice packages:")
required_packages = ["pyttsx3", "gtts", "playsound", "SpeechRecognition"]
missing_packages = []

for package in required_packages:
    try:
        importlib.import_module(package)
        print(f"  ✓ {package} is installed")
    except ImportError:
        print(f"  ✗ {package} is NOT installed")
        missing_packages.append(package)

if missing_packages:
    print(f"\nMissing packages: {', '.join(missing_packages)}")
    install = input("Install missing packages now? (y/n): ")
    if install.lower() == 'y':
        for package in missing_packages:
            print(f"Installing {package}...")
            os.system(f"pip install {package}")

# Test pyttsx3 directly
print("\n2. Testing pyttsx3 (offline TTS engine):")
try:
    import pyttsx3
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    print(f"  ✓ pyttsx3 initialized successfully")
    print(f"  ✓ Found {len(voices)} voices")
    
    for i, voice in enumerate(voices):
        print(f"    Voice {i}: {voice.name} ({voice.id})")
    
    # Try to speak
    print("\n  Testing voice output - you should hear speech...")
    engine.say("JARVIS voice test is now running")
    engine.runAndWait()
    
    result = input("\n  Did you hear the test speech? (y/n): ")
    if result.lower() == 'n':
        print("  ✗ Voice output failed - checking audio devices...")
        
        # Check audio devices
        if platform.system() == 'Windows':
            print("\n3. Checking Windows audio devices:")
            os.system("powershell -c \"Get-CimInstance Win32_SoundDevice | Select Name, Status\"")
        else:
            print("\n3. Please check your audio devices manually")
    else:
        print("  ✓ Voice output is working correctly")
        
except Exception as e:
    print(f"  ✗ Error with pyttsx3: {str(e)}")

# Check JARVIS server configuration
print("\n4. Checking JARVIS configuration:")
env_file = ".env"
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    if "ENABLE_VOICE=true" in env_content:
        print("  ✓ Voice is enabled in .env file")
    else:
        print("  ✗ Voice is not enabled in .env file")
        with open(env_file, 'a') as f:
            f.write("\n# Voice configuration\nENABLE_VOICE=true\nVOICE_PROVIDER=pyttsx3\n")
        print("    - Added voice configuration to .env file")
else:
    print("  ✗ .env file not found")

# Check API support
print("\n5. Testing direct voice API:")
try:
    import requests
    response = requests.post(
        "http://localhost:8000/",
        json={"method": "generate_voice", "params": {"text": "This is a voice test"}},
        timeout=10
    )
    
    if response.status_code == 200:
        print(f"  ✓ Voice API responded with status 200")
        data = response.json()
        print(f"  Response: {data}")
        
        if "error" in data:
            print(f"  ✗ Server reported error: {data['error']}")
    else:
        print(f"  ✗ Voice API failed with status {response.status_code}")
except Exception as e:
    print(f"  ✗ Error testing voice API: {str(e)}")

# Summary & Recommendations
print("\n===== DIAGNOSTIC SUMMARY =====")
print("Based on the tests, here are recommendations:")

print("""
1. Make sure your speakers/headphones are connected and not muted
2. Restart the JARVIS server after any configuration changes
3. If pyttsx3 test worked but JARVIS speech doesn't:
   - Check server logs for voice-related errors
   - Try using gTTS instead (change VOICE_PROVIDER=gtts in .env)
4. If nothing works, try adding these lines to your .env file:
   
   ENABLE_VOICE=true
   VOICE_PROVIDER=pyttsx3
   VOICE_RATE=150
   VOICE_VOLUME=1.0
   
   Then restart the server (stop_jarvis.bat then jarvis_launcher.bat)
""")

input("\nPress Enter to exit...") 