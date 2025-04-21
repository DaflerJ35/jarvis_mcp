@echo off
echo Installing JARVIS voice capabilities...

:: Install required packages
echo Installing voice packages...
pip install pyttsx3 gtts playsound pydub SpeechRecognition

:: Check for installation success
python -c "import pyttsx3" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install voice packages.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo Voice capabilities installed successfully!
echo To use voice features, restart JARVIS server if it's already running.
pause 