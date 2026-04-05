# Project EA - Root Cause Analysis and Comprehensive Fixes

## Executive Summary

After deep architectural analysis, I've identified **three fundamental flaws** in the data flow architecture that cause all reported issues. These are not superficial bugs but core design problems in how historical months, roll number updates, and VETO persistence interact.

---

## Issue #1: Historical Months Not Displaying (e.g., Feb 2026, Mar 26)

### Root Cause
The `getMonthAwareStudent()` function (line 15256) uses `month_roster_profiles` to display historical student data. When a student's roll number is updated:

1. **What gets updated:**
   - Global `students` array (new roll)
   - Current/future `month_roster_profiles` (new roll)

2. **What DOESN'T get updated:**
   - Historical `month_roster_profiles` (frozen with old roll)

3. **The Failure Chain:**
   ```
   Student Ayush: EA24D01 → EA25D20 (roll updated)
   
   Feb 2026 month_roster_profiles:
   - Still has: { roll: "EA24D01", name: "Ayush", ... }
   
   Scoreboard renders Feb 2026:
   - Looks up student by current roll: "EA25D20"
   - Searches Feb 2026 profiles for "EA25D20"
   - FAILS (only has "EA24D01")
   - Falls back to current student object
   - Returns student WITHOUT historical profile
   - Result: Student doesn't appear or appears with wrong data
   ```

### Why This Breaks Everything
- Historical months rely on `month_roster_profiles` for frozen snapshots
- When profile lookup fails, the function returns the current student object
- This causes the scoreboard to use current data instead of historical data
- Excel-imported totals are ignored because the historical flag isn't set correctly

---

## Issue #2: VETO Usage (VVV) Erased After Hard Refresh

### Root Cause
The VETO display has a **race condition** in the pull-repair-save-render cycle:

1. **The Broken Flow:**
   ```
   Hard Refresh Triggered
   ↓
   mergeScoreRowsForAuthoritativePull() runs (line 16028)
   ↓
   Completely REPLACES current-month scores with server data
   ↓
   Server data has NO VETO notes (they're in leadership table)
   ↓
   repairLeaderDirectAppointmentState() runs (line 10816)
   ↓
   Reconstructs VETO usage from leadership table
   ↓
   Saves repaired state to localStorage
   ↓
   Scoreboard renders
   ↓
   BUT: Renders with PRE-REPAIR pulled data (no VVV)
   ↓
   Next refresh: Pull wipes VVV again
   ```

2. **The Timing Problem:**
   - `getLeaderDirectAppointmentUsageMap()` only runs for current month (line 13709)
   - The map is built from `data.leadership` records
   - The map overlays missing VETO notes (lines 13812-13833)
   - But the authoritative pull happens BEFORE the overlay
   - The overlay is temporary and doesn't persist to the score rows

### Why VVV Keeps Disappearing
- Leadership posts with `source: 'leader_veto_direct'` are preserved
- But the score rows lose their VETO notes during pull
- The repair function adds them back temporarily
- The scoreboard renders before the repair is complete
- Next pull wipes them again

---

## Issue #3: Feb 2026 Scoreboard Wrong Order (Ayush on Top)

### Root Cause
This is a **compound failure** from Issue #1:

1. **The Cascade:**
   ```
   Ayush roll updated: EA24D01 → EA25D20
   ↓
   Feb 2026 profile lookup fails (Issue #1)
   ↓
   getMonthAwareStudent() returns current student object
   ↓
   Scoreboard processes scores for Ayush
   ↓
   Historical filter checks (line 13734):
   - isHistoricalMonth = true
   - Filters for excel_total_score notes
   ↓
   BUT: Profile lookup failed, so historical context is lost
   ↓
   hasHistoricalMonthlyTotal flag NOT set correctly
   ↓
   Line 14050 check fails:
   if (isHistoricalMonthKey(month) && row.hasHistoricalMonthlyTotal) {
       total = parseInt(row.monthlyImportedTotal, 10) || 0;
   }
   ↓
   Uses CURRENT accumulated scores instead of Feb 2026 total
   ↓
   Ayush appears at top with inflated score
   ```

2. **Why Rehmetun Loses Top Position:**
   - Rehmetun's profile lookup succeeds (roll unchanged)
   - Gets correct historical total from Excel import
   - But Ayush's current scores are higher than historical totals
   - Sorting by total puts Ayush first

---

## Comprehensive Fix Strategy

### Fix #1: Enhanced Historical Profile Lookup

**Location:** `getMonthAwareStudent()` function (line 15256)

**Strategy:**
1. Keep current roll-based lookup as primary
2. Add fallback for historical months:
   - Check if month is historical
   - If current roll lookup fails
   - Search for student by studentId in that month's scores
   - Match profile by name (since name doesn't change)
3. This ensures students with updated rolls can still find their historical profiles

**Implementation:**
```javascript
// After line 15260 (let profile = effectiveMap.get(currentRoll);)
// Add historical month fallback lookup by studentId + name matching
```

### Fix #2: VETO Persistence in Score Rows

**Location:** Multiple points in the pull/repair/save cycle

**Strategy:**
1. Ensure `repairLeaderDirectAppointmentState()` runs BEFORE pull merge
2. Persist VETO notes directly into score rows, not just overlay
3. Make leadership-based VETO reconstruction part of the merge process
4. Add VETO notes to score rows during save, not just during render

**Implementation:**
```javascript
// Modify pull flow to:
// 1. Pull server data
// 2. Repair VETO state from leadership
// 3. Merge repaired state (not raw server state)
// 4. Save merged result
// 5. Render
```

### Fix #3: Historical Month Profile Index

**Location:** `mergeStudentRecordsPreservingId()` function (line 11520)

**Strategy:**
1. When merging student records with roll updates
2. Create dual-index in historical month_roster_profiles
3. Keep both old roll and new roll pointing to same profile
4. This allows lookup by either roll number
5. Prevents historical month display breakage

**Implementation:**
```javascript
// In historical month profiles, maintain:
// - Primary entry with new roll
// - Alias entry with old roll (same data)
// Both point to same student profile
```

---

## Implementation Priority

1. **Fix #1 (Historical Profile Lookup)** - Highest priority
   - Fixes Issue #1 and Issue #3 directly
   - Enables historical months to display correctly
   - Restores Feb 2026 proper ordering

2. **Fix #2 (VETO Persistence)** - High priority
   - Fixes Issue #2 directly
   - Ensures VVV badges persist across refreshes
   - Prevents data loss during pull operations

3. **Fix #3 (Dual-Index Profiles)** - Medium priority
   - Prevents future occurrences of Issue #1
   - Makes system resilient to roll number changes
   - Improves long-term data integrity

---

## Testing Checklist

After implementing fixes:

1. **Historical Month Display:**
   - [ ] Feb 2026 shows all students correctly
   - [ ] Mar 26 shows all students correctly
   - [ ] Students with updated rolls appear in historical months
   - [ ] Historical totals match Excel imports

2. **VETO Persistence:**
   - [ ] Mar 28, 2026 shows Leader VVV badges
   - [ ] Mar 29, 2026 shows Leader VVV badges
   - [ ] Hard refresh preserves VVV badges
   - [ ] Cross-browser shows same VVV counts

3. **Scoreboard Ordering:**
   - [ ] Feb 2026 shows Rehmetun at top (not Ayush)
   - [ ] Historical month rankings match Excel data
   - [ ] Roll number updates don't affect historical rankings

---

## Files to Modify

1. `app/static/offline_scoreboard.html`
   - Line 15256: `getMonthAwareStudent()` function
   - Line 16028: `mergeScoreRowsForAuthoritativePull()` function
   - Line 10816: `repairLeaderDirectAppointmentState()` function
   - Line 11520: `mergeStudentRecordsPreservingId()` function

---

## Conclusion

These are not simple bugs but **architectural design flaws** in how the system handles:
- Historical data immutability
- Student identity across time
- VETO state persistence
- Data synchronization

The fixes address the root causes, not symptoms, ensuring long-term stability and data integrity.
