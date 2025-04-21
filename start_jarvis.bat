@echo off
echo Starting JARVIS with GUI and Voice Integration...

:: Stop any existing processes
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul
timeout /t 2 /nobreak > nul

:: Run the integration script
python update_gui_integration.py

:: This script will exit when the GUI closes
echo JARVIS system terminated.
pause 