@echo off
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║   🚀 EXCEL ACADEMY LEADERSHIP BOARD - LAUNCHER 🚀            ║
echo ║         Offline Student Scoring System                        ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Change to project directory
cd /d "C:\Users\sujit\Desktop\Project EA"

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found. Creating...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if Flask is installed
python -m pip show flask >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Installing Flask and dependencies...
    pip install -r requirements.txt
)

REM Start Flask server
echo.
echo ✅ Starting Flask server...
echo ⏳ Please wait while the server starts...
echo.
echo ═══════════════════════════════════════════════════════════════
echo 📊 Server Information:
echo ═══════════════════════════════════════════════════════════════
echo.
echo   🌐 System URL: http://127.0.0.1:5000/scoreboard/offline
echo   📱 Mobile Access: http://[YOUR_PC_IP]:5000/scoreboard/offline
echo   ⏹️  To stop: Press Ctrl+C in this window
echo.
echo ═══════════════════════════════════════════════════════════════
echo.

REM Open browser and start server
timeout /t 2 /nobreak
start http://127.0.0.1:5000/scoreboard/offline

REM Run Flask
python run.py
