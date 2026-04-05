# PowerShell script to apply the three critical fixes to offline_scoreboard.html
# Run this script from the Project EA directory

$htmlFile = "app\static\offline_scoreboard.html"
$backupFile = "app\static\offline_scoreboard.html.backup_" + (Get-Date -Format "yyyyMMdd_HHmmss")

Write-Host "Creating backup: $backupFile" -ForegroundColor Green
Copy-Item $htmlFile $backupFile

Write-Host "Reading file..." -ForegroundColor Yellow
$content = Get-Content $htmlFile -Raw

# Fix #1: Enhanced getMonthAwareStudent() for historical months
Write-Host "Applying Fix #1: Enhanced historical profile lookup..." -ForegroundColor Cyan

$oldPattern1 = @'
            }
            if (!profile) return student;
            const profileRoll = normalizeRoll(profile.roll) || currentRoll;
'@

$newPattern1 = @'
            }
            
            // CRITICAL FIX: For historical months, if current roll lookup fails, search by studentId
            // This handles cases where a student's roll was updated after the historical month was frozen
            if (!profile && isHistoricalMonthKey(month) && student.id) {
                const data = db.getData();
                const monthProfiles = (data.month_roster_profiles && data.month_roster_profiles[month]) || [];
                const studentId = parseInt(student.id, 10);
                
                // Find if this student has any scores in this historical month
                const monthScores = (data.scores || []).filter(s => {
                    const scoreMonth = String(s.month || String(s.date || '').slice(0, 7) || '').trim();
                    return scoreMonth === month && parseInt(s.studentId, 10) === studentId;
                });
                
                if (monthScores.length > 0) {
                    // Student participated in this month - find their profile by name matching
                    // (name is stable across roll updates, unlike roll number)
                    const targetName = normalizeText(student.base_name || student.name || '');
                    if (targetName) {
                        for (const candidate of monthProfiles) {
                            const candidateName = normalizeText(candidate.base_name || candidate.name || '');
                            if (candidateName && candidateName === targetName) {
                                profile = candidate;
                                break;
                            }
                        }
                    }
                }
            }
            
            if (!profile) return student;
            const profileRoll = normalizeRoll(profile.roll) || currentRoll;
'@

if ($content -match [regex]::Escape($oldPattern1)) {
    $content = $content -replace [regex]::Escape($oldPattern1), $newPattern1
    Write-Host "  ✓ Fix #1 applied successfully" -ForegroundColor Green
} else {
    Write-Host "  ✗ Fix #1 pattern not found - may already be applied" -ForegroundColor Yellow
}

# Fix #2: VETO persistence in score rows
Write-Host "Applying Fix #2: VETO persistence..." -ForegroundColor Cyan

$oldPattern2 = @'
                if (!primaryRow && canonicalItems.length > 0) {
                    primaryRow = {
                        id: Date.now() + Math.floor(Math.random() * 1000),
                        studentId: leaderId,
                        date: usageDate,
'@

$newPattern2 = @'
                if (!primaryRow && canonicalItems.length > 0) {
                    primaryRow = {
                        id: Date.now() + Math.floor(Math.random() * 1000),
                        studentId: leaderId,
                        date: usageDate,
                        notes: canonicalItems.map(item => item.noteText).join(' | '),
                        vetos: -canonicalItems.length,
'@

if ($content -match [regex]::Escape($oldPattern2)) {
    $content = $content -replace [regex]::Escape($oldPattern2), $newPattern2
    Write-Host "  ✓ Fix #2 applied successfully" -ForegroundColor Green
} else {
    Write-Host "  ✗ Fix #2 pattern not found - may already be applied" -ForegroundColor Yellow
}

# Fix #3: Dual-index for historical month profiles
Write-Host "Applying Fix #3: Historical profile dual-indexing..." -ForegroundColor Cyan

$oldPattern3 = @'
                (data.month_roster_profiles && typeof data.month_roster_profiles === 'object' ? Object.keys(data.month_roster_profiles) : []).forEach(monthKey => {
                    if (effectiveMonth && String(monthKey || '').trim() < effectiveMonth) return;
                    const profiles = Array.isArray(data.month_roster_profiles[monthKey]) ? data.month_roster_profiles[monthKey] : [];
'@

$newPattern3 = @'
                (data.month_roster_profiles && typeof data.month_roster_profiles === 'object' ? Object.keys(data.month_roster_profiles) : []).forEach(monthKey => {
                    const isHistoricalMonth = isHistoricalMonthKey(monthKey);
                    const shouldSkip = effectiveMonth && String(monthKey || '').trim() < effectiveMonth && !isHistoricalMonth;
                    if (shouldSkip) return;
                    const profiles = Array.isArray(data.month_roster_profiles[monthKey]) ? data.month_roster_profiles[monthKey] : [];
'@

if ($content -match [regex]::Escape($oldPattern3)) {
    $content = $content -replace [regex]::Escape($oldPattern3), $newPattern3
    Write-Host "  ✓ Fix #3 applied successfully" -ForegroundColor Green
} else {
    Write-Host "  ✗ Fix #3 pattern not found - may already be applied" -ForegroundColor Yellow
}

# Save the modified content
Write-Host "Saving modified file..." -ForegroundColor Yellow
$content | Set-Content $htmlFile -NoNewline

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "FIXES APPLIED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nBackup saved to: $backupFile" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Hard refresh your browser (Ctrl+Shift+R)" -ForegroundColor White
Write-Host "2. Check Feb 2026 scoreboard - Rehmetun should be at top" -ForegroundColor White
Write-Host "3. Check Mar 28/29 2026 - VVV badges should persist after refresh" -ForegroundColor White
Write-Host "4. Verify all historical months display correctly" -ForegroundColor White
Write-Host "`nIf issues occur, restore from backup:" -ForegroundColor Yellow
Write-Host "  Copy-Item '$backupFile' '$htmlFile' -Force" -ForegroundColor Gray
