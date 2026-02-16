@echo off
REM Realtime LAN Cluster Launcher for EA System
cd /d "%~dp0"

if "%EA_TIMEZONE%"=="" set "EA_TIMEZONE=Asia/Kolkata"
if "%SYNC_SHARED_KEY%"=="" set "SYNC_SHARED_KEY=EA_SYNC_917511"
if "%PORT%"=="" set /p PORT=Enter port [5000]: 
if "%PORT%"=="" set "PORT=5000"
if "%SYNC_PEERS%"=="" set /p SYNC_PEERS=Enter peer server URL(s) comma-separated (optional): 

echo.
echo Starting EA LAN realtime server...
echo PORT=%PORT%
echo EA_TIMEZONE=%EA_TIMEZONE%
echo SYNC_PEERS=%SYNC_PEERS%

echo.
if exist "%~dp0.venv\Scripts\python.exe" (
  "%~dp0.venv\Scripts\python.exe" run.py
) else (
  python run.py
)
pause
