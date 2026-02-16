param(
    [string]$TaskName = "ProjectEA_OffsiteSync_2230",
    [string]$ProjectRoot = "C:\Users\sujit\OneDrive\Desktop\Project EA",
    [string]$OffsiteRoot = "C:\Users\sujit\OneDrive\ProjectEA_Offsite_Backups",
    [string]$Time24h = "22:30",
    [int]$KeepDays = 60
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ProjectRoot)) {
    throw "Project root not found: $ProjectRoot"
}

$syncScript = Join-Path $ProjectRoot "backup_offsite_sync.ps1"
if (-not (Test-Path $syncScript)) {
    throw "Offsite sync script not found: $syncScript"
}

$parts = $Time24h.Split(":")
if ($parts.Count -ne 2) {
    throw "Time24h must be HH:mm format. Example: 22:30"
}
$hour = [int]$parts[0]
$minute = [int]$parts[1]
if ($hour -lt 0 -or $hour -gt 23 -or $minute -lt 0 -or $minute -gt 59) {
    throw "Invalid Time24h value: $Time24h"
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$syncScript`" -ProjectRoot `"$ProjectRoot`" -OffsiteRoot `"$OffsiteRoot`" -KeepDays $KeepDays" `
    -WorkingDirectory $ProjectRoot

$trigger = New-ScheduledTaskTrigger -Daily -At ([DateTime]::Today.AddHours($hour).AddMinutes($minute))

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Project EA offsite backup sync to OneDrive/cloud folder" | Out-Null

Write-Output "Scheduled task created: $TaskName"
Write-Output "Time: $Time24h daily"
Write-Output "ProjectRoot: $ProjectRoot"
Write-Output "OffsiteRoot: $OffsiteRoot"
Write-Output "KeepDays: $KeepDays"

