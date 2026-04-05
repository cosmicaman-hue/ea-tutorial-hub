# Add frozen month protection to offline_scoreboard.html
$htmlFile = "app\static\offline_scoreboard.html"
$backupFile = "app\static\offline_scoreboard.html.backup_frozen_protection_" + (Get-Date -Format "yyyyMMdd_HHmmss")

Write-Host "Creating backup: $backupFile" -ForegroundColor Green
Copy-Item $htmlFile $backupFile

Write-Host "Reading file..." -ForegroundColor Yellow
$content = Get-Content $htmlFile -Raw

# Find the canMutateMonthSnapshot function and enhance it
$oldFunction = @'
        function canMutateMonthSnapshot(monthKey, options = {}) {
            if (!isHistoricalMonthKey(monthKey)) return true;
            return options.allowHistoricalWrite === true;
        }
'@

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

if ($content -match [regex]::Escape($oldFunction)) {
    $content = $content -replace [regex]::Escape($oldFunction), $newFunction
    Write-Host "✓ Enhanced canMutateMonthSnapshot function" -ForegroundColor Green
} else {
    Write-Host "✗ canMutateMonthSnapshot pattern not found" -ForegroundColor Yellow
}

# Add frozen month check to saveScore function
$saveScorePattern = @'
        async function saveScore() {
            const studentId = document.getElementById('scoreStudent').value;
'@

$saveScoreReplacement = @'
        async function saveScore() {
            const studentId = document.getElementById('scoreStudent').value;
            const scoreDate = getElementValue('scoreDate');
            const scoreMonth = scoreDate ? scoreDate.substring(0, 7) : getCurrentMonthKey();
            
            // Check if month is frozen
            const data = db.getData();
            const frozenMonths = data.frozen_months || {};
            if (frozenMonths[scoreMonth] && frozenMonths[scoreMonth].hardened === true) {
                showMessage(`Cannot add scores to ${scoreMonth} - this month is frozen and hardened`, 'error');
                return;
            }
'@

if ($content -match [regex]::Escape($saveScorePattern)) {
    $content = $content -replace [regex]::Escape($saveScorePattern), $saveScoreReplacement
    Write-Host "✓ Added frozen month check to saveScore" -ForegroundColor Green
} else {
    Write-Host "✗ saveScore pattern not found" -ForegroundColor Yellow
}

# Save the modified content
Write-Host "Saving modified file..." -ForegroundColor Yellow
$content | Set-Content $htmlFile -NoNewline

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "FROZEN MONTH PROTECTION ADDED!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nBackup saved to: $backupFile" -ForegroundColor Cyan
Write-Host "`nFeb 2026 is now protected from modifications" -ForegroundColor White
