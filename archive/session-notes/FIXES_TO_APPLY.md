# Exact Code Fixes for Project EA Issues

## Fix #1: Enhanced getMonthAwareStudent() Function

**Location:** Line 15260 in `app/static/offline_scoreboard.html`

**Current Code (lines 15260-15272):**
```javascript
            let profile = effectiveMap.get(currentRoll);
            if (!profile) {
                const targetName = normalizeText(student.base_name || student.name || '');
                if (targetName) {
                    for (const candidate of effectiveMap.values()) {
                        const candidateName = normalizeText(candidate.base_name || candidate.name || '');
                        if (candidateName && candidateName === targetName) {
                            profile = candidate;
                            break;
                        }
                    }
                }
            }
```

**Replace With:**
```javascript
            let profile = effectiveMap.get(currentRoll);
            
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
            
            // Fallback: name-based lookup for all months (existing logic)
            if (!profile) {
                const targetName = normalizeText(student.base_name || student.name || '');
                if (targetName) {
                    for (const candidate of effectiveMap.values()) {
                        const candidateName = normalizeText(candidate.base_name || candidate.name || '');
                        if (candidateName && candidateName === targetName) {
                            profile = candidate;
                            break;
                        }
                    }
                }
            }
```

---

## Fix #2: VETO Persistence - Modify repairLeaderDirectAppointmentState()

**Location:** Line 10847-10870 in `app/static/offline_scoreboard.html`

**Current Code (lines 10847-10870):**
```javascript
                if (!primaryRow && canonicalItems.length > 0) {
                    primaryRow = {
                        id: Date.now() + Math.floor(Math.random() * 1000),
                        studentId: leaderId,
                        date: usageDate,
```

**Add After Line 10870 (inside the repair function):**
```javascript
                        // CRITICAL FIX: Persist VETO notes directly into the score row
                        // This ensures VVV badges survive hard refreshes and authoritative pulls
                        notes: canonicalItems.map(item => item.noteText).join(' | '),
                        vetos: -canonicalItems.length,
```

**Also Modify:** The section around line 10880 where existing rows are updated

**Find:**
```javascript
                if (primaryRow) {
                    const existingNotes = String(primaryRow.notes || '').trim();
```

**Add after this:**
```javascript
                    // Ensure VETO notes from leadership are persisted in score row
                    const canonicalNoteTexts = canonicalItems.map(item => String(item.noteText || '').trim());
                    const existingNoteParts = existingNotes.split('|').map(s => s.trim()).filter(Boolean);
                    const missingNotes = canonicalNoteTexts.filter(note => 
                        !existingNoteParts.some(existing => existing.toLowerCase().includes(note.toLowerCase()))
                    );
                    
                    if (missingNotes.length > 0) {
                        primaryRow.notes = existingNotes 
                            ? `${existingNotes} | ${missingNotes.join(' | ')}`
                            : missingNotes.join(' | ');
                        primaryRow.vetos = (parseInt(primaryRow.vetos, 10) || 0) - missingNotes.length;
                        changed = true;
                    }
```

---

## Fix #3: Preserve Historical Profiles During Roll Updates

**Location:** Line 11598-11626 in `app/static/offline_scoreboard.html`

**Current Code (lines 11598-11626):**
```javascript
                (data.month_roster_profiles && typeof data.month_roster_profiles === 'object' ? Object.keys(data.month_roster_profiles) : []).forEach(monthKey => {
                    if (effectiveMonth && String(monthKey || '').trim() < effectiveMonth) return;
                    const profiles = Array.isArray(data.month_roster_profiles[monthKey]) ? data.month_roster_profiles[monthKey] : [];
```

**Replace the effectiveMonth check with:**
```javascript
                (data.month_roster_profiles && typeof data.month_roster_profiles === 'object' ? Object.keys(data.month_roster_profiles) : []).forEach(monthKey => {
                    const isHistoricalMonth = isHistoricalMonthKey(monthKey);
                    const shouldSkip = effectiveMonth && String(monthKey || '').trim() < effectiveMonth && !isHistoricalMonth;
                    if (shouldSkip) return;
                    
                    const profiles = Array.isArray(data.month_roster_profiles[monthKey]) ? data.month_roster_profiles[monthKey] : [];
```

**Then add after line 11625 (after the profile update loop):**
```javascript
                    // CRITICAL FIX: For historical months, create dual-index entry
                    // Keep both old roll and new roll pointing to same student
                    // This prevents historical month display breakage when rolls are updated
                    if (isHistoricalMonth && touched) {
                        const byRoll = new Map();
                        profiles.forEach(profile => {
                            if (!profile || typeof profile !== 'object') return;
                            const roll = normalizeRosterValue(profile.roll);
                            if (!roll) return;
                            byRoll.set(roll, profile);
                        });
                        
                        // Add old roll as alias if student roll was updated
                        if (sourceRoll !== targetRoll) {
                            const targetProfile = byRoll.get(targetRoll);
                            if (targetProfile && !byRoll.has(sourceRoll)) {
                                // Create alias entry with old roll pointing to same data
                                byRoll.set(sourceRoll, { ...targetProfile, roll: sourceRoll });
                            }
                        }
                        
                        data.month_roster_profiles[monthKey] = Array.from(byRoll.values());
                    }
```

---

## How to Apply These Fixes

### Method 1: Manual Edit (Recommended)
1. Open `app/static/offline_scoreboard.html` in a text editor
2. Navigate to each line number mentioned above
3. Carefully replace the code sections with the new code
4. Save the file

### Method 2: Search and Replace
1. Use your editor's search function to find the exact code blocks
2. Replace with the new versions
3. Verify all changes before saving

---

## Verification Steps

After applying fixes, test:

1. **Historical Months:**
   - View Feb 2026 scoreboard
   - Verify all students appear (including Ayush)
   - Check that Rehmetun is at top, not Ayush

2. **VETO Badges:**
   - View Mar 28, 2026 scoreboard
   - Check Leader has VVV badges
   - Hard refresh (Ctrl+Shift+R)
   - Verify VVV badges still show

3. **Cross-Browser:**
   - Open in Edge and DuckDuckGo
   - Verify both show same VETO counts
   - Verify both show same historical month data

---

## Why These Fixes Work

**Fix #1:** Enables historical profile lookup by studentId + name matching when roll lookup fails. This ensures students with updated rolls can still find their historical profiles.

**Fix #2:** Persists VETO notes directly into score rows during repair, not just as a temporary overlay. This ensures VVV badges survive hard refreshes.

**Fix #3:** Creates dual-index entries in historical month profiles, allowing lookup by both old and new roll numbers. This prevents future breakage when rolls are updated.

---

## Rollback Plan

If issues occur, restore from backup:
```
instance/offline_scoreboard_data.json (your data is safe)
```

The HTML file can be reverted by undoing the changes.
