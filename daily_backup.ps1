param(
    [string]$ProjectRoot = ".",
    [int]$KeepDays = 30
)

$ErrorActionPreference = "Stop"

Set-Location $ProjectRoot

$instanceDir = Join-Path (Get-Location) "instance"
if (-not (Test-Path $instanceDir)) {
    throw "instance folder not found: $instanceDir"
}

$sourceJson = Join-Path $instanceDir "offline_scoreboard_data.json"
$sourceDb = Join-Path $instanceDir "ea_tutorial.db"

if (-not (Test-Path $sourceJson)) {
    throw "Source data file not found: $sourceJson"
}

$backupRoot = Join-Path $instanceDir "ops_daily_backups"
$jsonBackupDir = Join-Path $backupRoot "json"
$dbBackupDir = Join-Path $backupRoot "db"

New-Item -ItemType Directory -Force -Path $jsonBackupDir | Out-Null
New-Item -ItemType Directory -Force -Path $dbBackupDir | Out-Null

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$jsonTarget = Join-Path $jsonBackupDir "offline_scoreboard_data_$stamp.json"
Copy-Item -LiteralPath $sourceJson -Destination $jsonTarget -Force

if (Test-Path $sourceDb) {
    $dbTarget = Join-Path $dbBackupDir "ea_tutorial_$stamp.db"
    Copy-Item -LiteralPath $sourceDb -Destination $dbTarget -Force
}

$cutoff = (Get-Date).AddDays(-1 * [Math]::Abs($KeepDays))
Get-ChildItem -LiteralPath $jsonBackupDir -File -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt $cutoff } |
    Remove-Item -Force -ErrorAction SilentlyContinue

Get-ChildItem -LiteralPath $dbBackupDir -File -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt $cutoff } |
    Remove-Item -Force -ErrorAction SilentlyContinue

$latestJson = Get-Item -LiteralPath $jsonTarget
Write-Output ("Daily backup complete: " + $latestJson.FullName)
Write-Output ("KeepDays: " + $KeepDays)
