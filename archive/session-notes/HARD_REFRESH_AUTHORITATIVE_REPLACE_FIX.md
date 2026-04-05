# 🔧 Critical Hard-Refresh Bug Fix - Stale VETO Data in Admin View

## Problem

After hard-refresh, scoreboard displays stale VETO values:
- Leader: 10V (should be 5V)
- Co-Leader: 9V (should be 6V)
- Group C CR: 7V (should be 5V)
- Previous CR: 3V (should be 1V)

Even though server data is correct, the admin view gets stale values.

## Root Cause

**In the `pullFromServer()` function**, the code decides whether to do a "merge" or "authoritative replace":

```javascript
// OLD BUGGY CODE (Line ~15592-15607):
const preferAuthoritativeServerApply = roleNeedsAuthoritativeSync && !hasPendingLocalWrites;
// For admins: roleNeedsAuthoritativeSync = false
// So: preferAuthoritativeServerApply = false

if (shouldApplyRemote) {
    applyRemoteSnapshot(latest.data, newestIso, showToast, {
        preferServerConflicts: preferAuthoritativeServerApply,     // FALSE
        authoritativeReplace: preferAuthoritativeServerApply,      // FALSE
        ...
    });
}
```

**The bug:** For admins, `authoritativeReplace=false` even on hard-refresh (`forceFull=true`).

This causes `applyRemoteSnapshot` to use **merge logic**:
- It merges local cache (stale VETO values) with server data
- The merge keeps the stale local cache values
- Result: stale VETOs display

## Solution

**Force `authoritativeReplace=true` when `forceFull=true` (hard-refresh)**:

```javascript
// NEW FIXED CODE (Line ~15593-15609):
const useAuthoritativeReplace = forceFull || preferAuthoritativeServerApply;

if (shouldApplyRemote) {
    applyRemoteSnapshot(latest.data, newestIso, showToast, {
        preferServerConflicts: useAuthoritativeReplace || preferAuthoritativeServerApply,
        authoritativeReplace: useAuthoritativeReplace,  // ← NOW TRUE on hard-refresh!
        ...
    });
}
```

When `authoritativeReplace=true`, `applyRemoteSnapshot` does:

```javascript
if (authoritativeReplace) {
    mergedData = {
        ...baseline,
        ...serverData,    // ← Server data REPLACES everything
    };
}
```

This completely replaces stale local cache with fresh server data, including correct:
- veto_count
- role_veto_count  
- veto_tracking

## Changes Made

**File**: `app/static/offline_scoreboard.html`

**Lines**: ~15593-15609

**What Changed**:
1. Added variable: `const useAuthoritativeReplace = forceFull || preferAuthoritativeServerApply;`
2. Changed `authoritativeReplace: preferAuthoritativeServerApply` → `authoritativeReplace: useAuthoritativeReplace`
3. Also changed `preferServerConflicts` to use the new variable for safety

## How It Works Now

```
Hard-Refresh Sequence (FIXED):

1. DOMContentLoaded fires
2. pullFromServer(false, true) called
   ├─ forceFull = true
   ├─ Fetches fresh server data with correct VETOs
   └─ Calls applyRemoteSnapshot with:
      └─ authoritativeReplace: true  ← MY FIX!

3. applyRemoteSnapshot runs with authoritativeReplace=true
   ├─ Does: mergedData = { ...baseline, ...serverData, ... }
   ├─ Server data spreads OVER local cache
   ├─ Stale VETO values are discarded
   └─ Fresh server VETOs are used (5V, 6V, 5V, 1V)

4. db.saveData(mergedData) saves fresh data to localStorage
5. Display loads fresh data
6. User sees: Leader 5V ✓, Co-Leader 6V ✓, etc.
```

## Testing Checklist

After this fix, hard-refresh should show:
- [ ] Leader: **5V** (not 10V)
- [ ] Co-Leader: **6V** (not 9V)
- [ ] Group C CR: **5V** (not 7V)
- [ ] Previous CR: **1V** (not 3V)
- [ ] All post-holders show correct VETOs
- [ ] Values persist after F5 refresh
- [ ] No data corruption occurs

## Data Files

✅ **No data files modified**
- instance/offline_scoreboard_data.json - Unchanged
- All backups - Unchanged
- VETO checksums - Unchanged

## Other Protections Still Active

✅ `anti_corruption_check.py` - Validates on startup
✅ `veto_integrity_guard.py` - Validates sync payloads
✅ `VETO_SYSTEM_RESTORED.md` - Recovery procedures
✅ Hardened veto_tracking system

## Summary

**The optimization wasn't the only culprit** — there was also a fundamental logic bug in how admins pull fresh data on hard-refresh. This fix ensures that:

1. Hard-refresh with `forceFull=true` ALWAYS does authoritative replace
2. Stale local cache is completely discarded
3. Fresh server data (with correct VETOs) is used
4. No merge logic with stale values
