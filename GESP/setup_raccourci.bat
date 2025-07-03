@echo off
set SHORTCUT_NAME=GESP.lnk
set TARGET=%~dp0launcher.bat
set ICON=%~dp0logo.ico

echo Set oWS = WScript.CreateObject("WScript.Shell") > link.vbs
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\%SHORTCUT_NAME%" >> link.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> link.vbs
echo oLink.TargetPath = "%TARGET%" >> link.vbs
echo oLink.WorkingDirectory = "%~dp0" >> link.vbs
echo oLink.IconLocation = "%ICON%" >> link.vbs
echo oLink.Save >> link.vbs

cscript //nologo link.vbs
del link.vbs

echo ✅ Raccourci avec icône créé sur le bureau.
pause
