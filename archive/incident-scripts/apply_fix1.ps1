# Apply Fix #1: Enhanced historical profile lookup
$htmlFile = "app\static\offline_scoreboard.html"

Write-Host "Reading file..." -ForegroundColor Yellow
$lines = Get-Content $htmlFile

# Find the line "if (!profile) return student;" around line 15277
$targetLineIndex = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s+if \(\!profile\) return student;') {
        $targetLineIndex = $i
        Write-Host "Found target line at index: $i (line $($i+1))" -ForegroundColor Cyan
        break
    }
}

if ($targetLineIndex -eq -1) {
    Write-Host "ERROR: Could not find target line" -ForegroundColor Red
    exit 1
}

# Insert the fix code before this line
$fixCode = @'
            
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
'@

$newLines = @()
$newLines += $lines[0..($targetLineIndex - 1)]
$newLines += $fixCode -split "`n"
$newLines += $lines[$targetLineIndex..($lines.Count - 1)]

Write-Host "Writing modified file..." -ForegroundColor Yellow
$newLines | Set-Content $htmlFile

Write-Host "`n✓ Fix #1 applied successfully!" -ForegroundColor Green
Write-Host "Total lines added: $($fixCode -split "`n" | Measure-Object).Count" -ForegroundColor Cyan
