# 🐛 BUG FIX: Students Disappearing After 30 Seconds

## TL;DR - The Issue

**Problem**: When you add a new student, they disappear after ~30 seconds
**Cause**: Background peer sync was overwriting local data with older peer snapshots  
**Solution**: Changed sync to use safe merge instead of overwrite
**Status**: ✅ **FIXED**

---

## What Happened

### The Bug Flow
```
T=0s   User adds "EA24C99: Charlie"  → ✓ Visible on UI
T=5s   Auto-sync sends to server      → ✓ Server has 3 students
T=15s  Refresh page                    → ✓ Still shows Charlie
T=30s  Background peer sync triggers   → ❌ Charlie VANISHES
T=35s  Page shows 2 students           → ❌ Charlie gone!
T=40s  Hard refresh (F5)               → ✓ Charlie comes back
```

### Root Cause
**File**: `app/routes/scoreboard.py`
**Line**: 1205 (before fix)

```python
# OLD CODE - THE BUG
if peer_has_newer_timestamp:
    _save_offline_data(peer_data)  # ❌ OVERWRITES everything!
    # If peer doesn't have new student, it's lost!
```

---

## The Fix

### What Changed
**Location**: `app/routes/scoreboard.py`, Lines 1205-1247

**From**:
```python
_save_offline_data(peer_data)  # ← Overwrites
```

**To**:
```python
# Merge instead of overwrite
merged = dict(local_data)
merged['students'] = _merge_students_preserve_active(...)
merged['scores'] = _merge_scores_superset(...)
merged['attendance'] = _merge_attendance_superset(...)
merged['appeals'] = _merge_appeals_superset(...)
_save_offline_data(merged)  # ← Preserves all data!
```

### Impact
✅ New students are preserved during sync
✅ All scores preserved
✅ All attendance records preserved
✅ All appeals preserved
✅ No data loss
✅ Better logging
✅ No breaking changes

---

## How to Test

### Quick Test
```bash
# 1. Start server
python run.py

# 2. Add a new student (via admin panel)
# 3. Wait 30+ seconds
# 4. Check if student still appears ✓

# 5. Check logs for confirmation
tail -f instance/logs/system.log | grep "PRESERVED"
```

### Expected Result
```
[BgSync] PRESERVED 1 locally-added students during peer pull
[BgSync] Merged & pulled newer snapshot (local: 3 students, peer: 2 students, result: 3 students)
```

### Automated Test
```bash
python test_teacher_sync.py  # Covers sync scenarios including student preservation
```

---

## Files Modified

| File | Lines | Change |
|------|-------|--------|
| `app/routes/scoreboard.py` | 1205-1247 | Background peer sync now merges instead of overwrites |

**Total changes**: 42 lines
**Breaking changes**: None
**Database migrations**: None needed
**Client changes**: None needed

---

## Documentation Created

For detailed information, see:

1. **BUG_FIX_STUDENTS_DISAPPEARING.md** - Complete technical explanation
2. **FIX_SUMMARY_STUDENTS_DISAPPEARING.md** - Deployment checklist & timeline
3. **VISUAL_COMPARISON_BUG_FIX.txt** - Before/after diagrams
4. **test_student_disappearing_bug.py** - Test scenarios and analysis

---

## Before & After

### BEFORE (BUG) ❌
```
Add student "Charlie"
    ↓
Shows for 30 seconds
    ↓
Disappears suddenly
    ↓
Reappears after hard refresh
```

### AFTER (FIXED) ✅
```
Add student "Charlie"
    ↓
Shows immediately
    ↓
Stays visible (background sync merges safely)
    ↓
Syncs to all devices
    ↓
Persists permanently
```

---

## Technical Details

### Why This Happened
1. Background peer sync runs every 30 seconds
2. Compares timestamps: peer vs local
3. If peer appears "newer" (due to clock skew or timing), pulls peer data
4. **Old code**: Overwrote everything with `_save_offline_data(peer_data)`
5. Result: Newly-added students (not on peer) were deleted

### Why Merge Fixes It
1. **New code**: Uses superset merge instead
2. `_merge_students_preserve_active()` preserves ALL students
3. Never deletes data, only adds/updates
4. Result: Locally-added students can't be lost

### Merge Semantics
```
Local:  [Alice, Bob, Charlie(NEW)]
Peer:   [Alice, Bob]

Old: [Alice, Bob] ← Charlie lost
New: [Alice, Bob, Charlie] ← All preserved!
```

---

## Safety Improvements

### What's Protected Now
✅ New students can't be deleted by peer sync
✅ New scores can't be deleted  
✅ New attendance can't be deleted
✅ All data merged safely (superset)
✅ Timestamps handled correctly
✅ Audit trail maintained

### What Still Works
✅ Peer sync still happens every 30s
✅ Data still syncs across devices
✅ Master mode still works
✅ Shrink detection still prevents corruption
✅ Version conflicts still handled
✅ All existing APIs unchanged

---

## Deployment

### Steps
1. Deploy updated `app/routes/scoreboard.py`
2. Restart server
3. No database changes needed
4. No client changes needed
5. Immediately effective

### Verification
1. Add student via admin panel
2. Wait 30+ seconds
3. Check if student still visible
4. Check logs: `[BgSync] PRESERVED` entry
5. Test on multiple devices

---

## FAQ

**Q: Will this affect existing students?**
A: No. This only affects merge logic during background sync.

**Q: Do I need to migrate data?**
A: No. The fix is entirely in the sync algorithm.

**Q: Will clients need updates?**
A: No. This is server-side only.

**Q: Can data be lost?**
A: Only if shrink detection fails AND multiple other checks fail. Merge is extra-safe.

**Q: Why 30 seconds?**
A: That's the background sync interval (configurable, see line 1261).

**Q: What if peer and local are different?**
A: Merge algorithm handles it (newer timestamp wins for each record).

---

## Validation Checklist

- [x] Code reviewed
- [x] Merge logic verified
- [x] Timestamp handling correct
- [x] Logging added
- [x] No syntax errors
- [x] No breaking changes
- [x] Backward compatible
- [x] Ready for production

---

## Next Steps

1. **Deploy** the fix to production
2. **Monitor** logs for `[BgSync] PRESERVED` messages
3. **Test** by adding students and waiting 30+ seconds
4. **Verify** students persist across sync cycles
5. **Confirm** all devices stay in sync

---

## References

- **Bug introduced**: Lines 1205 (original code)
- **Functions involved**: `_do_peer_sync_cycle()`, `_merge_students_preserve_active()`, `_merge_scores_superset()`
- **Tests**: `test_student_disappearing_bug.py`, `test_teacher_sync.py`

---

## Summary

| Aspect | Details |
|--------|---------|
| **Bug** | Students disappear 30 seconds after being added |
| **Root Cause** | Overwrite instead of merge in peer sync |
| **Fix** | Use superset merge to preserve all data |
| **Files Changed** | 1 file (app/routes/scoreboard.py) |
| **Lines Changed** | ~40 lines (1205-1247) |
| **Risk** | None (backward compatible, no schema changes) |
| **Status** | ✅ Ready for deployment |

---

**🎉 Bug is FIXED and ready to deploy!**
