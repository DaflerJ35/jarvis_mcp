@echo off
echo Starting JARVIS with full movie-like capabilities...

:: Stop any existing processes
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul
timeout /t 2 /nobreak > nul

:: Install required packages
echo Installing advanced dependencies...
pip install PyQt5 PyQtWebEngine requests fastapi uvicorn pydantic colorama python-dotenv
pip install SpeechRecognition pyaudio pyttsx3 gtts playsound pygame pywin32 psutil pyautogui
pip install comtypes pycaw win10toast numpy

:: Create temp directory for audio files if it doesn't exist
if not exist temp mkdir temp

:: Start the enhanced JARVIS server in the background
echo Starting JARVIS Advanced Server with movie-like capabilities...
start /min cmd /c "python jarvis_advanced_server.py > jarvis_advanced.log 2>&1"

:: Wait for server to initialize
echo Waiting for JARVIS initialization...
timeout /t 6 /nobreak > nul

:: Show welcome message
echo.
echo ===============================================
echo  J.A.R.V.I.S - Just A Rather Very Intelligent System
echo  Advanced Edition with Movie-Like Capabilities
echo ===============================================
echo.
echo JARVIS is now active and listening!
echo.
echo Capabilities:
echo  - Voice Recognition (say "Hey Jarvis" to activate)
echo  - System Control (open apps, web search, etc.)
echo  - Natural Language Processing
echo  - Advanced Voice Synthesis
echo.
echo Try these commands:
echo  - "Jarvis, what time is it?"
echo  - "Open Chrome"
echo  - "Search for the latest news"
echo  - "Show system status"
echo  - "Take a screenshot"
echo.
echo JARVIS is running in the background.
echo You can close this window and JARVIS will continue running.
echo To stop JARVIS, run stop_jarvis.bat
echo.
pause 