# Fix Feb 2026 display issue - disable strict Excel filtering for Feb 2026
$htmlFile = "app\static\offline_scoreboard.html"
$backupFile = "app\static\offline_scoreboard.html.backup_feb2026_fix_" + (Get-Date -Format "yyyyMMdd_HHmmss")

Write-Host "Creating backup: $backupFile" -ForegroundColor Green
Copy-Item $htmlFile $backupFile

Write-Host "Reading file..." -ForegroundColor Yellow
$lines = Get-Content $htmlFile

# Find the historical month filtering logic (around line 13738)
$targetIndex = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match 'if \(isHistoricalMonth\) \{' -and $lines[$i+1] -match 'const noteLow') {
        $targetIndex = $i
        Write-Host "Found historical month filter at line $($i+1)" -ForegroundColor Cyan
        break
    }
}

if ($targetIndex -eq -1) {
    Write-Host "ERROR: Pattern not found" -ForegroundColor Red
    exit 1
}

# Replace the strict filtering with Feb 2026 exception
$newCode = @'
                        if (isHistoricalMonth) {
                            // Feb 2026 contains regular scores (not Excel imports), so skip strict filtering
                            if (String(month || '').trim() === '2026-02') {
                                // Allow all scores for Feb 2026
                            } else {
                                // For other historical months, enforce Excel-only filtering
                                const noteLow = noteText.toLowerCase();
                                const isExcelTotal = noteLow.startsWith('excel_total_score') || noteLow.startsWith('excel_total_from_dates');
                                const isExcelDaily = noteLow.startsWith('excel_daily_score');
                                const isExcelStar = noteLow.startsWith('excel_star_usage');
                                // Historical months should render strictly from Excel-imported rows only.
                                // This prevents old legacy rows from inflating totals.
                                if (!isExcelTotal && !isExcelDaily && !isExcelStar) {
                                    return;
                                }
                            }
                        }
'@

$newLines = @()
$newLines += $lines[0..($targetIndex - 1)]
$newLines += $newCode -split "`n"
# Skip the old filtering code (lines 13738-13748, which is 11 lines)
$newLines += $lines[($targetIndex + 11)..($lines.Count - 1)]

Write-Host "Writing modified file..." -ForegroundColor Yellow
$newLines | Set-Content $htmlFile

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "FEB 2026 DISPLAY FIX APPLIED!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nBackup saved to: $backupFile" -ForegroundColor Cyan
Write-Host "`nFeb 2026 will now display all scores (not just Excel imports)" -ForegroundColor White
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Hard refresh browser (Ctrl+Shift+R)" -ForegroundColor White
Write-Host "2. Navigate to Feb 2026 scoreboard" -ForegroundColor White
Write-Host "3. Verify students show correct scores (not 0)" -ForegroundColor White
