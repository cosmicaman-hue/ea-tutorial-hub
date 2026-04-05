# Add frozen month protection - Version 2
$htmlFile = "app\static\offline_scoreboard.html"

Write-Host "Reading file..." -ForegroundColor Yellow
$lines = Get-Content $htmlFile

# Find canMutateMonthSnapshot function
$targetIndex = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match 'function canMutateMonthSnapshot') {
        $targetIndex = $i
        Write-Host "Found canMutateMonthSnapshot at line $($i+1)" -ForegroundColor Cyan
        break
    }
}

if ($targetIndex -eq -1) {
    Write-Host "ERROR: Function not found" -ForegroundColor Red
    exit 1
}

# Replace the function (lines targetIndex to targetIndex+3)
$newFunction = @'
        function canMutateMonthSnapshot(monthKey, options = {}) {
            if (!isHistoricalMonthKey(monthKey)) return true;
            
            // Check if month is frozen/hardened
            const data = db.getData();
            const frozenMonths = data.frozen_months || {};
            const monthFrozen = frozenMonths[monthKey];
            
            if (monthFrozen && monthFrozen.hardened === true && monthFrozen.allow_modifications === false) {
                console.warn(`[FROZEN MONTH] ${monthKey} is hardened and cannot be modified`);
                return false;
            }
            
            return options.allowHistoricalWrite === true;
        }
'@

$newLines = @()
$newLines += $lines[0..($targetIndex - 1)]
$newLines += $newFunction -split "`n"
# Skip the old function (4 lines)
$newLines += $lines[($targetIndex + 4)..($lines.Count - 1)]

Write-Host "Writing modified file..." -ForegroundColor Yellow
$newLines | Set-Content $htmlFile

Write-Host "`n✓ Frozen month protection added!" -ForegroundColor Green
Write-Host "Feb 2026 is now protected from modifications" -ForegroundColor Cyan
