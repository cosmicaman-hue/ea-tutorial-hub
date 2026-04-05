@echo off
REM EA Tutorial Hub - Development Server Launcher
REM Starts the app with Flask auto-reload for local code editing.

cd /d "%~dp0"
set "EA_TIMEZONE=Asia/Kolkata"
set "EA_MASTER_MODE=1"
set "FLASK_ENV=development"
set "FLASK_DEBUG=1"
set "FLASK_USE_RELOADER=1"
set "EA_USE_WAITRESS=0"
set "EA_SKIP_STARTUP_RESTORE=1"
if not defined SYNC_SHARED_KEY set "SYNC_SHARED_KEY=EA_SYNC_KEY_917511_2026"

if exist "%~dp0.venv\Scripts\python.exe" (
  "%~dp0.venv\Scripts\python.exe" run.py
) else (
  python run.py
)
pause
