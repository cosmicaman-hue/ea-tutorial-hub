# Realtime LAN Cluster Launcher for EA System
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

if (-not $env:EA_TIMEZONE) { $env:EA_TIMEZONE = 'Asia/Kolkata' }
if (-not $env:SYNC_SHARED_KEY) { $env:SYNC_SHARED_KEY = 'EA_SYNC_917511' }
if (-not $env:PORT) {
    $portInput = Read-Host 'Enter port [5000]'
    $env:PORT = if ([string]::IsNullOrWhiteSpace($portInput)) { '5000' } else { $portInput }
}
if (-not $env:SYNC_PEERS) {
    $env:SYNC_PEERS = Read-Host 'Enter peer server URL(s) comma-separated (optional)'
}

Write-Host "Starting EA LAN realtime server..." -ForegroundColor Cyan
Write-Host "PORT=$($env:PORT)"
Write-Host "EA_TIMEZONE=$($env:EA_TIMEZONE)"
Write-Host "SYNC_PEERS=$($env:SYNC_PEERS)"

$pythonPath = Join-Path $ScriptDir '.venv\Scripts\python.exe'
if (-not (Test-Path $pythonPath)) { $pythonPath = 'python' }
& $pythonPath run.py
