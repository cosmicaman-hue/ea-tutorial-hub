@echo off
REM EA Tutorial Hub - Server Launcher
REM This script starts the Flask application for network access

cd /d "%~dp0"
set "EA_TIMEZONE=Asia/Kolkata"
set "EA_MASTER_MODE=1"
set "FLASK_ENV=production"
set "FLASK_DEBUG=0"
set "FLASK_USE_RELOADER=0"
REM Optional: set peer server(s) for automatic server-to-server sync.
REM Example: set "SYNC_PEERS=http://192.168.0.164:5000"
if not defined SYNC_PEERS set "SYNC_PEERS=http://192.168.0.163:5000"
if not defined SYNC_SHARED_KEY set "SYNC_SHARED_KEY=EA_SYNC_KEY_917511_2026"

if exist "%~dp0.venv\Scripts\python.exe" (
  "%~dp0.venv\Scripts\python.exe" run.py
) else (
  python run.py
)
pause
