# Backup LAN Server Launcher (PowerShell)
# Run this on a second LAN PC to host a mirror of the EA system.

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$pythonPath = Join-Path $ScriptDir '.venv\Scripts\python.exe'
if (-not (Test-Path $pythonPath)) {
    $pythonPath = 'python'
}

# Backup PC can run on same LAN port if hosted separately; override with BACKUP_PORT if needed.
if (-not $env:BACKUP_PORT) {
    $env:BACKUP_PORT = '5000'
}
$env:EA_TIMEZONE = if ($env:EA_TIMEZONE) { $env:EA_TIMEZONE } else { 'Asia/Kolkata' }
$env:EA_MASTER_MODE = '0'
if (-not $env:SYNC_PEERS) { $env:SYNC_PEERS = 'http://192.168.0.183:5000' } # Primary LAN server
if (-not $env:SYNC_SHARED_KEY) { $env:SYNC_SHARED_KEY = 'EA_SYNC_KEY_917511_2026' }

& $pythonPath run.py
