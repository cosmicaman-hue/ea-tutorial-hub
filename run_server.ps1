# EA Tutorial Hub - Server Launcher (PowerShell)
# This script starts the Flask application for network access

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$env:EA_TIMEZONE = if ($env:EA_TIMEZONE) { $env:EA_TIMEZONE } else { 'Asia/Kolkata' }
$env:EA_MASTER_MODE = '1'
$env:FLASK_ENV = 'production'
$env:FLASK_DEBUG = '0'
$env:FLASK_USE_RELOADER = '0'
# Auto-forward every Master Update to the Render cloud server.
# Change this URL if your Render service name differs.
if (-not $env:SYNC_PEERS) { $env:SYNC_PEERS = 'https://ea-tutorial-hub.onrender.com' }
if (-not $env:SYNC_SHARED_KEY) { $env:SYNC_SHARED_KEY = 'EA_SYNC_KEY_917511_2026' }

$pythonPath = Join-Path $ScriptDir '.venv\Scripts\python.exe'
if (-not (Test-Path $pythonPath)) {
    $pythonPath = 'python'
}

& $pythonPath run.py
