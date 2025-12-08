@echo off
setlocal enabledelayedexpansion

REM ========================================
REM EA Tutorial Hub - Simple Server Launcher
REM ========================================
REM This is a simplified version that's more reliable
REM Just double-click to start!

color 0A
cls

echo.
echo ====================================
echo  EA Tutorial Hub - Server Launcher
echo ====================================
echo.

REM Get current directory
cd /d "%~dp0"
set CURRENT_DIR=%cd%

echo Project Location: %CURRENT_DIR%
echo.

REM Check if Python exists
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ERROR: Python not found!
    echo.
    echo Please install Python from:
    echo https://www.python.org/downloads/
    echo.
    echo IMPORTANT: During installation, CHECK:
    echo - "Add Python to PATH"
    echo.
    echo Then restart this computer and try again.
    echo.
    pause
    exit /b 1
)

REM Show Python version
echo Python installed:
python --version
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment (this takes ~30 seconds)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        color 0C
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo.
echo Starting Flask application...
echo.

REM Activate venv and run Flask
call .\.venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    color 0C
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies if needed
if not exist ".venv\Lib\site-packages\flask" (
    echo Installing dependencies (this takes ~1 minute)...
    pip install -r requirements.txt -q
    if %errorlevel% neq 0 (
        color 0C
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo ====================================
echo  Application Starting...
echo ====================================
echo.
echo NOTE: Keep this window OPEN for the server to run
echo.
echo To find your server IP, open PowerShell and run:
echo   ipconfig
echo.
echo Look for IPv4 Address (something like 192.168.0.163)
echo.
echo Then on another PC, open browser and go to:
echo   http://[YOUR_SERVER_IP]:5000
echo.
echo Press Ctrl+C here to stop the server
echo ====================================
echo.

REM Run Flask
python run.py

color 0F
pause
