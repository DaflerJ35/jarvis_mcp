@echo off
echo Starting JARVIS system...

:: First stop any running JARVIS servers
echo Checking for existing JARVIS processes...
taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq hidden" 2>nul
taskkill /F /IM python.exe /FI "COMMANDLINE eq *jarvis_server.py*" 2>nul
taskkill /F /IM python.exe /FI "COMMANDLINE eq *simple_server.py*" 2>nul
taskkill /F /IM python.exe /FI "COMMANDLINE eq *server.py*" 2>nul

:: Wait a moment for processes to fully terminate
timeout /t 2 /nobreak > nul

:: Check if server file exists
if not exist jarvis_server.py (
    echo ERROR: jarvis_server.py not found!
    echo Looking for alternative server files...
    
    if exist simple_server.py (
        echo Found simple_server.py, using that instead.
        set SERVER_FILE=simple_server.py
    ) else if exist server.py (
        echo Found server.py, using that instead.
        set SERVER_FILE=server.py
    ) else (
        echo No server file found. Please ensure one of these files exists:
        echo - jarvis_server.py (recommended)
        echo - simple_server.py
        echo - server.py
        pause
        exit /b 1
    )
) else (
    set SERVER_FILE=jarvis_server.py
)

:: Install required packages
echo Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to install required packages.
    echo Please make sure you have Python and pip installed correctly.
    pause
    exit /b 1
)

:: Start the server in background
echo Starting JARVIS server with %SERVER_FILE%...
start /b python %SERVER_FILE%
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to start JARVIS server.
    pause
    exit /b 1
)

:: Wait for server to initialize
echo Waiting for server initialization...
timeout /t 5 /nobreak > nul

:: Check if server is responding on port 8000
curl -s http://localhost:8000/ > nul
if %ERRORLEVEL% NEQ 0 (
    :: Try alternate port 8080
    curl -s http://localhost:8080/ > nul
    if %ERRORLEVEL% NEQ 0 (
        echo Warning: JARVIS server may not be running properly.
        echo The GUI will still launch, but functionality may be limited.
        echo If you encounter issues, please restart the application.
    ) else (
        echo Connected to JARVIS server on port 8080.
    )
) else (
    echo Connected to JARVIS server on port 8000.
)

:: Start the GUI
echo Launching JARVIS interface...
python jarvis_gui.py

:: Exit
echo JARVIS system terminated.
exit /b 0 