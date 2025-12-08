@echo off
REM START_SYSTEM.bat - Simplest possible launcher
REM This file launches the Flask server in the background

cd /d "C:\Users\sujit\Desktop\Project EA"

REM Start Python in background
start "" pythonw -m flask run --host=0.0.0.0 --port=5000
timeout /t 3 /nobreak

REM Open the HTML launcher in default browser
start LAUNCHER.html

exit
