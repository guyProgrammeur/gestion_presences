@echo off
cd /d %~dp0

:: Vérifie si l'app est déjà en cours
tasklist /FI "IMAGENAME eq MonAppRapports.exe" | find /I "MonAppRapports.exe" > nul
if %errorlevel%==0 (
    echo MonAppRapports.exe est déjà lancé. On ne fait rien.
) else (
    echo Lancement de MonAppRapports.exe...
    start "" "MonAppRapports.exe"
    timeout /t 3 /nobreak > nul
    start "" "http://127.0.0.1:8000/accounts/login/"
)
