@echo off
echo Starting JARVIS system in background mode...

:: Change to the JARVIS directory
cd /d "%~dp0"

:: First stop any running JARVIS servers to avoid port conflicts
taskkill /F /IM pythonw.exe 2>nul
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *server*" 2>nul
timeout /t 2 /nobreak > nul

:: Check if server file exists
if not exist jarvis_server.py (
    if exist minimal_server.py (
        set SERVER_FILE=minimal_server.py
    ) else if exist simple_server.py (
        set SERVER_FILE=simple_server.py
    ) else if exist server.py (
        set SERVER_FILE=server.py
    ) else (
        echo ERROR: No server file found!
        echo JARVIS failed to start at %time% on %date% - Missing server file > jarvis_error.log
        exit /b 1
    )
) else (
    set SERVER_FILE=jarvis_server.py
)

:: Install required packages (silent mode)
echo Installing dependencies...
if exist requirements.txt (
    pip install -q -r requirements.txt
) else (
    pip install -q PyQt5 PyQtWebEngine requests fastapi uvicorn pydantic colorama python-dotenv sse-starlette
)

:: Create empty .env file if doesn't exist
if not exist .env (
    echo # JARVIS environment settings > .env
    echo SERVER_PORT=8000 >> .env
    echo Creating default .env file
)

:: Start the server in hidden window
echo Starting JARVIS server with %SERVER_FILE%...
start /b "" pythonw %SERVER_FILE%

:: Create a small notification
echo JARVIS server started successfully at %time% on %date% with %SERVER_FILE% > jarvis_last_start.log

:: Exit silently
exit 