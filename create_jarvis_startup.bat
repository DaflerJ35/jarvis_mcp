@echo off
echo Setting up JARVIS to start automatically with Windows...

:: Get the current directory path
set CURRENT_DIR=%~dp0
set JARVIS_PATH=%CURRENT_DIR%jarvis_autostart.bat

:: Create shortcut in the Windows Startup folder
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = oWS.SpecialFolders("Startup") ^& "\JARVIS_Autostart.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%JARVIS_PATH%" >> CreateShortcut.vbs
echo oLink.WindowStyle = 7 >> CreateShortcut.vbs
echo oLink.Description = "JARVIS Automatic Startup" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%CURRENT_DIR%" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript //nologo CreateShortcut.vbs
del CreateShortcut.vbs

echo JARVIS has been added to Windows startup!
echo It will now start automatically when you turn on your PC.
pause 