@echo off
REM Backup LAN Server Launcher
REM Run this on a second LAN PC to host a mirror of the EA system.

cd /d "%~dp0"
set "BACKUP_PORT=5000"
set "EA_TIMEZONE=Asia/Kolkata"
set "EA_MASTER_MODE=0"
set "FLASK_ENV=production"
set "FLASK_DEBUG=0"
set "FLASK_USE_RELOADER=0"
REM Set this to primary server URL for auto replication from backup -> primary.
REM Example: set "SYNC_PEERS=http://192.168.0.183:5000"
if not defined SYNC_PEERS set "SYNC_PEERS=http://192.168.0.183:5000"
if not defined SYNC_SHARED_KEY set "SYNC_SHARED_KEY=EA_SYNC_KEY_917511_2026"
if exist "%~dp0.venv\Scripts\python.exe" (
  "%~dp0.venv\Scripts\python.exe" run.py
) else (
  python run.py
)
pause
