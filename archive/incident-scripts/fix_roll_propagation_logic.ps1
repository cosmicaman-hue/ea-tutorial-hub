# Fix roll number propagation to respect frozen/hardened months
$htmlFile = "app\static\offline_scoreboard.html"
$backupFile = "app\static\offline_scoreboard.html.backup_roll_propagation_fix_" + (Get-Date -Format "yyyyMMdd_HHmmss")

Write-Host "Creating backup: $backupFile" -ForegroundColor Green
Copy-Item $htmlFile $backupFile

Write-Host "Reading file..." -ForegroundColor Yellow
$lines = Get-Content $htmlFile

# Find the month_roster_profiles update section (around line 11600)
$targetIndex = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match 'data\.month_roster_profiles.*Object\.keys' -and 
        $lines[$i+1] -match 'const isHistoricalMonth') {
        $targetIndex = $i + 1
        Write-Host "Found month_roster_profiles update at line $($i+1)" -ForegroundColor Cyan
        break
    }
}

if ($targetIndex -eq -1) {
    Write-Host "ERROR: Pattern not found" -ForegroundColor Red
    exit 1
}

# Replace the shouldSkip logic to check frozen months
$newCode = @'
                    const isHistoricalMonth = isHistoricalMonthKey(monthKey);
                    
                    // Check if month is frozen/hardened - NEVER update frozen months for upgradations
                    const data = db.getData();
                    const frozenMonths = data.frozen_months || {};
                    const monthFrozen = frozenMonths[monthKey];
                    const isFrozenMonth = monthFrozen && monthFrozen.hardened === true && monthFrozen.allow_modifications === false;
                    
                    // Skip if:
                    // 1. Month is before effectiveMonth AND not a technical correction (effectiveMonth set means upgradation)
                    // 2. Month is frozen/hardened (always skip for upgradations, only Historical Editor can modify)
                    const shouldSkip = (effectiveMonth && String(monthKey || '').trim() < effectiveMonth) || isFrozenMonth;
                    if (shouldSkip) return;
'@

$newLines = @()
$newLines += $lines[0..($targetIndex - 1)]
$newLines += $newCode -split "`n"
# Skip old lines (3 lines: isHistoricalMonth, shouldSkip, if shouldSkip)
$newLines += $lines[($targetIndex + 3)..($lines.Count - 1)]

Write-Host "Writing modified file..." -ForegroundColor Yellow
$newLines | Set-Content $htmlFile

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "ROLL PROPAGATION FIX APPLIED!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nBackup saved to: $backupFile" -ForegroundColor Cyan
Write-Host "`nFrozen months (like Feb 2026) are now protected from roll number upgradations" -ForegroundColor White
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Undo Ayush and Tanu roll number changes" -ForegroundColor White
Write-Host "2. Verify Feb 2026 displays correctly" -ForegroundColor White
Write-Host "3. After April 2026, redo upgradations properly" -ForegroundColor White
