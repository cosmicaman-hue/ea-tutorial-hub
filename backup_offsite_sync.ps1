param(
    [string]$ProjectRoot = ".",
    [string]$OffsiteRoot = "C:\Users\sujit\OneDrive\ProjectEA_Offsite_Backups",
    [int]$KeepDays = 60
)

$ErrorActionPreference = "Stop"

Set-Location $ProjectRoot

$instanceDir = Join-Path (Get-Location) "instance"
$localRoot = Join-Path $instanceDir "ops_daily_backups"
$jsonLocal = Join-Path $localRoot "json"
$dbLocal = Join-Path $localRoot "db"

if (-not (Test-Path $jsonLocal)) {
    throw "Local backup folder not found: $jsonLocal"
}

$jsonOff = Join-Path $OffsiteRoot "json"
$dbOff = Join-Path $OffsiteRoot "db"
New-Item -ItemType Directory -Force -Path $jsonOff | Out-Null
New-Item -ItemType Directory -Force -Path $dbOff | Out-Null

# Copy only new/changed files efficiently.
robocopy $jsonLocal $jsonOff *.json /E /XO /R:2 /W:2 /NFL /NDL /NJH /NJS /NC /NS | Out-Null
if (Test-Path $dbLocal) {
    robocopy $dbLocal $dbOff *.db /E /XO /R:2 /W:2 /NFL /NDL /NJH /NJS /NC /NS | Out-Null
}

$cutoff = (Get-Date).AddDays(-1 * [Math]::Abs($KeepDays))
Get-ChildItem -LiteralPath $jsonOff -File -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt $cutoff } |
    Remove-Item -Force -ErrorAction SilentlyContinue

Get-ChildItem -LiteralPath $dbOff -File -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt $cutoff } |
    Remove-Item -Force -ErrorAction SilentlyContinue

$latest = Get-ChildItem -LiteralPath $jsonOff -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latest) {
    Write-Output ("Offsite sync complete. Latest JSON: " + $latest.FullName)
} else {
    Write-Output "Offsite sync complete. No JSON files found."
}
Write-Output ("OffsiteRoot: " + $OffsiteRoot)
Write-Output ("KeepDays: " + $KeepDays)

