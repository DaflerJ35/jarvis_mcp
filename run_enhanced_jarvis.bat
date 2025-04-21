@echo off
echo Starting Enhanced JARVIS with voice capabilities...

:: First stop any running JARVIS servers
echo Stopping existing JARVIS processes...
taskkill /F /IM pythonw.exe 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *server*" 2>nul
timeout /t 2 /nobreak > nul

:: Install required packages
echo Installing dependencies...
pip install fastapi uvicorn pydantic pyttsx3 gtts playsound pypiwin32 SpeechRecognition

:: Start the Enhanced JARVIS server in background
echo Starting Enhanced JARVIS server...
start /b python enhanced_jarvis_server.py

:: Wait for server to initialize
echo Waiting for server initialization...
timeout /t 5 /nobreak > nul

:: Launch the GUI
echo Launching JARVIS interface...
start python jarvis_gui.py

echo JARVIS system started. The server is running in the background.
echo You can close this window, and JARVIS will continue running.
pause 