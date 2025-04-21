@echo off
echo Removing JARVIS from Windows startup...

:: Create VBS script to remove the shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > RemoveShortcut.vbs
echo sLinkFile = oWS.SpecialFolders("Startup") ^& "\JARVIS_Autostart.lnk" >> RemoveShortcut.vbs
echo Set fso = CreateObject("Scripting.FileSystemObject") >> RemoveShortcut.vbs
echo If fso.FileExists(sLinkFile) Then >> RemoveShortcut.vbs
echo     fso.DeleteFile sLinkFile >> RemoveShortcut.vbs
echo     WScript.Echo "JARVIS removed from startup." >> RemoveShortcut.vbs
echo Else >> RemoveShortcut.vbs
echo     WScript.Echo "JARVIS was not found in startup." >> RemoveShortcut.vbs
echo End If >> RemoveShortcut.vbs
cscript //nologo RemoveShortcut.vbs
del RemoveShortcut.vbs

echo.
echo If you want to add JARVIS back to startup, run the create_jarvis_startup.bat script.
pause 