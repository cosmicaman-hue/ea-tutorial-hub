@echo off
REM START_SYSTEM.bat - Safe launcher
REM Uses run.py (single-instance lock + integrity guards), not flask run.

cd /d "%~dp0"
set "EA_TIMEZONE=Asia/Kolkata"
if not defined EA_MASTER_MODE set "EA_MASTER_MODE=1"
if not defined SYNC_PEERS set "SYNC_PEERS=http://192.168.0.163:5000"
if not defined SYNC_SHARED_KEY set "SYNC_SHARED_KEY=EA_SYNC_KEY_917511_2026"
set "FLASK_ENV=production"
set "FLASK_DEBUG=0"
set "FLASK_USE_RELOADER=0"

if exist "%~dp0.venv\Scripts\python.exe" (
  start "" "%~dp0.venv\Scripts\python.exe" run.py
) else (
  start "" python run.py
)

timeout /t 2 /nobreak >nul
start "" http://127.0.0.1:5000/scoreboard/offline
exit
