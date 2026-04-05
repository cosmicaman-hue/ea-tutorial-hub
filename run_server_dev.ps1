# EA Tutorial Hub - Development Server Launcher (PowerShell)
# Starts the app with Flask auto-reload for local code editing.

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$env:EA_TIMEZONE = if ($env:EA_TIMEZONE) { $env:EA_TIMEZONE } else { 'Asia/Kolkata' }
$env:EA_MASTER_MODE = '1'
$env:FLASK_ENV = 'development'
$env:FLASK_DEBUG = '1'
$env:FLASK_USE_RELOADER = '1'
$env:EA_USE_WAITRESS = '0'
$env:EA_SKIP_STARTUP_RESTORE = '1'
if (-not $env:SYNC_SHARED_KEY) { $env:SYNC_SHARED_KEY = 'EA_SYNC_KEY_917511_2026' }

$pythonPath = Join-Path $ScriptDir '.venv\Scripts\python.exe'
if (-not (Test-Path $pythonPath)) {
    $pythonPath = 'python'
}

& $pythonPath run.py
