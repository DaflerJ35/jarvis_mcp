@echo off
echo Starting JARVIS system on alternate port (8080)...

:: Check if server file exists
if not exist jarvis_server.py (
    echo ERROR: jarvis_server.py not found!
    echo Looking for alternative server files...
    
    if exist minimal_server.py (
        echo Found minimal_server.py, using that instead.
        set SERVER_FILE=minimal_server.py
    ) else if exist simple_server.py (
        echo Found simple_server.py, using that instead.
        set SERVER_FILE=simple_server.py
    ) else if exist server.py (
        echo Found server.py, using that instead.
        set SERVER_FILE=server.py
    ) else (
        echo No server file found. Please ensure one of these files exists:
        echo - jarvis_server.py (recommended)
        echo - minimal_server.py
        echo - simple_server.py
        echo - server.py
        pause
        exit /b 1
    )
) else (
    set SERVER_FILE=jarvis_server.py
)

:: Create/update .env with alternate port
echo # JARVIS Environment Configuration > .env
echo # Server configuration >> .env
echo SERVER_PORT=8080 >> .env
echo SERVER_HOST=0.0.0.0 >> .env
echo ENABLE_SSE=true >> .env
echo ENABLE_MCP=true >> .env
echo # MCP Path Configuration >> .env
echo MCP_SSE_PATH=/mcp/sse >> .env
echo STREAM_PATH=/stream >> .env
echo # Authentication (disabled by default) >> .env
echo AUTHENTICATION_REQUIRED=false >> .env
echo # Client permissions >> .env
echo ALLOWED_CLIENTS=cursor,claude >> .env
echo # Knowledge base configuration >> .env
echo ENABLE_KNOWLEDGE_BASE=true >> .env
echo KNOWLEDGE_DIR=./knowledge >> .env

echo Updated .env to use port 8080

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
echo Starting JARVIS server with %SERVER_FILE% on port 8080...
start /b python %SERVER_FILE%
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to start JARVIS server.
    pause
    exit /b 1
)

:: Wait for server to initialize
echo Waiting for server initialization...
timeout /t 5 /nobreak > nul

:: Check if server is responding
curl -s http://localhost:8080/ > nul
if %ERRORLEVEL% NEQ 0 (
    echo Warning: JARVIS server may not be running properly.
    echo The GUI will still launch, but functionality may be limited.
    echo If you encounter issues, please restart the application.
) else (
    echo Connected to JARVIS server on port 8080.
)

:: Start the GUI
echo Launching JARVIS interface...
python jarvis_gui.py

:: Exit
echo JARVIS system terminated.
exit /b 0 