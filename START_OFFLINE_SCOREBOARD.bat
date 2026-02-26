@echo off
echo.
echo ================================================================
echo    EXCEL ACADEMY LEADERSHIP BOARD - LAUNCHER
echo    Offline Student Scoring System
echo ================================================================
echo.

REM Change to project directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
echo Virtual environment not found. Creating...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if Flask is installed
python -m pip show flask >nul 2>&1
if errorlevel 1 (
echo Installing Flask and dependencies...
    pip install -r requirements.txt
)

REM Start Flask server
echo.
echo Starting Flask server...
echo ⏳ Please wait while the server starts...
echo.
echo ═══════════════════════════════════════════════════════════════
echo Server Information:
echo ═══════════════════════════════════════════════════════════════
echo.
echo   System URL: http://127.0.0.1:5000/scoreboard/offline
echo   Mobile Access: http://[YOUR_PC_IP]:5000/scoreboard/offline
echo   To stop: Press Ctrl+C in this window
echo.
echo ═══════════════════════════════════════════════════════════════
echo.

REM Open browser and start server
timeout /t 2 /nobreak
start "" http://127.0.0.1:5000/scoreboard/offline

REM Run server in production-safe mode
set "EA_TIMEZONE=Asia/Kolkata"
if not defined EA_MASTER_MODE set "EA_MASTER_MODE=1"
if not defined SYNC_PEERS set "SYNC_PEERS=http://192.168.0.163:5000"
if not defined SYNC_SHARED_KEY set "SYNC_SHARED_KEY=EA_SYNC_KEY_917511_2026"
set "FLASK_ENV=production"
set "FLASK_DEBUG=0"
set "FLASK_USE_RELOADER=0"
python run.py
