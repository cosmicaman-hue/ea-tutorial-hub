# 🚀 EXCEL ACADEMY LEADERSHIP BOARD - PowerShell Launcher
# Offline Student Scoring System - Auto-Start Script

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host "   EXCEL ACADEMY LEADERSHIP BOARD - LAUNCHER" -ForegroundColor Cyan
Write-Host "   Offline Student Scoring System" -ForegroundColor Cyan
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host ""

# Project directory
$ProjectDir = $PSScriptRoot
Set-Location $ProjectDir

Write-Host "Project Directory: $ProjectDir" -ForegroundColor Yellow
Write-Host "PowerShell Version: $($PSVersionTable.PSVersion.Major).$($PSVersionTable.PSVersion.Minor)" -ForegroundColor Yellow
Write-Host ""

# Virtual environment path
$VenvPath = Join-Path $ProjectDir ".venv"
$VenvActivate = Join-Path $VenvPath "Scripts" "Activate.ps1"

# Check virtual environment
if (-not (Test-Path $VenvPath)) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "Virtual environment created." -ForegroundColor Green
    Write-Host ""
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& $VenvActivate

# Check Flask
Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    $FlaskCheck = python -c "import flask; print('OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Flask installed" -ForegroundColor Green
    }
}
catch {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Write-Host "Dependencies installed" -ForegroundColor Green
}

# Print server info
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "SERVER INFORMATION:" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  System: http://127.0.0.1:5000/scoreboard/offline" -ForegroundColor Cyan
Write-Host "  Mobile: http://[YOUR_PC_IP]:5000/scoreboard/offline" -ForegroundColor Cyan
Write-Host "  To Stop: Press Ctrl+C" -ForegroundColor Yellow
Write-Host ""
Write-Host "════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Open browser
Write-Host "Opening browser in 2 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

$Url = "http://127.0.0.1:5000/scoreboard/offline"
Write-Host "Opening: $Url" -ForegroundColor Green
Start-Process $Url

# Start Flask
Write-Host ""
Write-Host "Starting server..." -ForegroundColor Green
Write-Host ""
Write-Host "────────────────────────────────────────────────────────────────" -ForegroundColor DarkCyan
Write-Host ""

$env:EA_TIMEZONE = if ($env:EA_TIMEZONE) { $env:EA_TIMEZONE } else { 'Asia/Kolkata' }
if (-not $env:EA_MASTER_MODE) { $env:EA_MASTER_MODE = '1' }
if (-not $env:SYNC_PEERS) { $env:SYNC_PEERS = 'http://192.168.0.163:5000' }
if (-not $env:SYNC_SHARED_KEY) { $env:SYNC_SHARED_KEY = 'EA_SYNC_KEY_917511_2026' }
$env:FLASK_ENV = 'production'
$env:FLASK_DEBUG = '0'
$env:FLASK_USE_RELOADER = '0'

python run.py
