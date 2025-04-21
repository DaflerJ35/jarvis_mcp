@echo off
echo Stopping all running JARVIS servers...

:: Kill any running Python processes related to JARVIS servers
taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq hidden" 2>nul
taskkill /F /IM python.exe /FI "COMMANDLINE eq *jarvis_server.py*" 2>nul
taskkill /F /IM python.exe /FI "COMMANDLINE eq *minimal_server.py*" 2>nul
taskkill /F /IM python.exe /FI "COMMANDLINE eq *simple_server.py*" 2>nul
taskkill /F /IM python.exe /FI "COMMANDLINE eq *server.py*" 2>nul

:: Wait a moment for processes to fully terminate
timeout /t 2 /nobreak > nul

:: Verify port 8000 is free
echo Checking if port 8000 is now available...
netstat -an | find "0.0.0.0:8000" > nul
if %ERRORLEVEL% EQU 0 (
    echo Warning: Port 8000 is still in use. Please close any applications using this port.
) else (
    echo Success: JARVIS servers stopped. Port 8000 is now available.
)

echo.
echo You can now start JARVIS again.
echo.
pause 