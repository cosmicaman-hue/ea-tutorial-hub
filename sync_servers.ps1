param(
    [string]$Primary = 'http://192.168.0.183:5000',
    [string]$Secondary = 'http://192.168.0.163:5000',
    [string]$SyncKey = 'EA_SYNC_KEY_917511_2026',
    [switch]$AllowSecondaryToPrimary,
    [int]$MinSafeStudentRoster = 25,
    [switch]$ForcePrimaryToSecondary
)

$ErrorActionPreference = 'Stop'

function Get-OfflineData($baseUrl) {
    $url = "$($baseUrl.TrimEnd('/'))/scoreboard/offline-data"
    try {
        $resp = Invoke-RestMethod -Uri $url -Method GET -TimeoutSec 8
        if ($null -eq $resp) {
            return [pscustomobject]@{ url = $url; status = 204; updated_at = $null; data = $null }
        }
        return [pscustomobject]@{ url = $url; status = 200; updated_at = $resp.updated_at; data = $resp.data }
    } catch {
        $status = $null
        try {
            if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
                $status = [int]$_.Exception.Response.StatusCode
            }
        } catch {
            $status = $null
        }
        if ($status) {
            return [pscustomobject]@{ url = $url; status = $status; updated_at = $null; data = $null }
        }
        throw
    }
}

function ToUnixTs($iso) {
    if ([string]::IsNullOrWhiteSpace($iso)) { return 0 }
    try {
        return [DateTimeOffset]::Parse($iso).ToUnixTimeSeconds()
    } catch {
        return 0
    }
}

function Push-OfflineData($targetBaseUrl, $payload, $syncKey) {
    $url = "$($targetBaseUrl.TrimEnd('/'))/scoreboard/offline-data"
    $body = @{ data = $payload } | ConvertTo-Json -Depth 100
    Invoke-RestMethod -Uri $url -Method POST -TimeoutSec 12 -ContentType 'application/json' -Headers @{
        'X-EA-Replicated' = '1'
        'X-EA-Sync-Key' = $syncKey
    } -Body $body | Out-Null
}

function Get-StudentCount($resp) {
    try {
        if ($null -eq $resp -or $null -eq $resp.data -or $null -eq $resp.data.students) { return 0 }
        return @($resp.data.students).Count
    } catch {
        return 0
    }
}

function Is-TinyRoster($count, $minSafe) {
    if ($minSafe -lt 1) { $minSafe = 1 }
    return ($count -gt 0 -and $count -lt $minSafe)
}

Write-Host "Checking servers..." -ForegroundColor Cyan
$a = $null
$b = $null
try { $a = Get-OfflineData $Primary; Write-Host "Primary reachable (HTTP $($a.status)): $Primary" -ForegroundColor Green } catch { Write-Host "Primary unreachable: $Primary ($($_.Exception.Message))" -ForegroundColor Yellow }
try { $b = Get-OfflineData $Secondary; Write-Host "Secondary reachable (HTTP $($b.status)): $Secondary" -ForegroundColor Green } catch { Write-Host "Secondary unreachable: $Secondary ($($_.Exception.Message))" -ForegroundColor Yellow }

if (-not $a -and -not $b) {
    Write-Host "Both servers unreachable. Nothing to sync." -ForegroundColor Red
    exit 1
}

if ($a -and -not $b) {
    Write-Host "Only primary reachable. No peer sync performed." -ForegroundColor Yellow
    exit 0
}

if ($b -and -not $a) {
    Write-Host "Only secondary reachable. No peer sync performed." -ForegroundColor Yellow
    exit 0
}

$aCount = Get-StudentCount $a
$bCount = Get-StudentCount $b
Write-Host "Roster counts: Primary=$aCount, Secondary=$bCount (MinSafe=$MinSafeStudentRoster)" -ForegroundColor Cyan

# Hard guardrail: If Secondary is in a known corrupt state (e.g. 20 students), always force Primary -> Secondary.
if ($ForcePrimaryToSecondary -or (Is-TinyRoster $bCount $MinSafeStudentRoster -and $aCount -ge $MinSafeStudentRoster)) {
    Write-Host "Secondary roster looks tiny/corrupt. Forcing Primary -> Secondary" -ForegroundColor Cyan
    Push-OfflineData -targetBaseUrl $Secondary -payload $a.data -syncKey $SyncKey
    Write-Host "Done." -ForegroundColor Green
    exit 0
}

# Safety: If Primary looks tiny/corrupt, do NOT auto-overwrite Primary unless explicitly allowed.
if ((Is-TinyRoster $aCount $MinSafeStudentRoster) -and $bCount -ge $MinSafeStudentRoster) {
    if ($AllowSecondaryToPrimary) {
        Write-Host "Primary roster looks tiny/corrupt. Syncing Secondary -> Primary (explicitly allowed)" -ForegroundColor Cyan
        Push-OfflineData -targetBaseUrl $Primary -payload $b.data -syncKey $SyncKey
        Write-Host "Done." -ForegroundColor Green
    } else {
        Write-Host "Primary roster looks tiny/corrupt, but reverse sync is blocked in safe mode." -ForegroundColor Yellow
        Write-Host "Use -AllowSecondaryToPrimary only after manual verification." -ForegroundColor Yellow
    }
    exit 0
}

$aTs = [Math]::Max([Math]::Max((ToUnixTs $a.updated_at), (ToUnixTs $a.data.server_updated_at)), (ToUnixTs $a.data.updated_at))
$bTs = [Math]::Max([Math]::Max((ToUnixTs $b.updated_at), (ToUnixTs $b.data.server_updated_at)), (ToUnixTs $b.data.updated_at))

if ($aTs -eq $bTs) {
    Write-Host "Servers already in sync by timestamp." -ForegroundColor Green
    exit 0
}

if ($aTs -gt $bTs) {
    Write-Host "Syncing Primary -> Secondary" -ForegroundColor Cyan
    if ($null -eq $a.data) {
        Write-Host "Primary returned no data; refusing to push." -ForegroundColor Red
        exit 1
    }
    Push-OfflineData -targetBaseUrl $Secondary -payload $a.data -syncKey $SyncKey
    Write-Host "Done." -ForegroundColor Green
} elseif ($bTs -gt $aTs -and $AllowSecondaryToPrimary) {
    Write-Host "Syncing Secondary -> Primary (explicitly allowed)" -ForegroundColor Cyan
    if ($null -eq $b.data) {
        Write-Host "Secondary returned no data; refusing to push." -ForegroundColor Red
        exit 1
    }
    Push-OfflineData -targetBaseUrl $Primary -payload $b.data -syncKey $SyncKey
    Write-Host "Done." -ForegroundColor Green
} else {
    Write-Host "Secondary appears newer, but reverse sync is blocked in safe mode." -ForegroundColor Yellow
    Write-Host "Use -AllowSecondaryToPrimary only after manual verification." -ForegroundColor Yellow
}
