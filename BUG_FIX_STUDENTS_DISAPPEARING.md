# Bug Fix: Students Disappearing After 30 Seconds

## 🔴 The Bug

**Symptom**: 
- Add a new student → Shows on scoreboard and everywhere
- Wait ~30 seconds
- Student disappears automatically!

**Timeline**:
```
T=0s   User adds student "Charlie"
       ✓ Shows on UI
       
T=5s   Local data syncs to server
       ✓ Server has 3 students (including Charlie)
       ✓ Shows on all devices
       
T=30s  Background peer sync runs (every 30 seconds)
       ❌ Gets old peer data (without Charlie)
       ❌ Overwrites local with peer data
       ❌ Charlie VANISHES
```

---

## 🔍 Root Cause

**Location**: `app/routes/scoreboard.py`, line 1205

```python
def _do_peer_sync_cycle(app):
    """Background sync runs every 30 seconds"""
    
    for peer in peers:
        # Fetch peer's snapshot
        peer_data = get_from_peer(peer)
        
        # Check if peer is newer
        if peer_stamp > local_stamp + 30 and peer_count >= min_students:
            if not _is_suspicious_student_shrink(local_data, peer_data):
                _save_offline_data(peer_data)  # ❌ BUG: OVERWRITES!
```

**The Problem**:
```
Local Data:  [Alice, Bob, Charlie(NEW)]    ← Just added
Peer Data:   [Alice, Bob]                   ← Stale/older
             
_save_offline_data(peer_data)  # ← Overwrites everything!

Result:      [Alice, Bob]                   ← Charlie LOST!
```

**Why it happens**:
1. Background sync compares timestamps
2. Due to clock skew or timing, peer might appear "newer"
3. Line 1205 blindly overwrites with `_save_offline_data(peer_data)`
4. Any locally-added students (not on peer) are lost

---

## ✅ The Fix

**Changed**: Lines 1201-1237 in `app/routes/scoreboard.py`

**From** (WRONG):
```python
if peer_stamp > local_stamp + 30 and peer_count >= min_students:
    if not _is_suspicious_student_shrink(local_data, peer_data):
        _save_offline_data(peer_data)  # ← OVERWRITES, loses local data!
```

**To** (CORRECT):
```python
if peer_stamp > local_stamp + 30 and peer_count >= min_students:
    if not _is_suspicious_student_shrink(local_data, peer_data):
        # CRITICAL FIX: Merge instead of overwrite
        merged = dict(local_data)
        
        # Superset merge key tables (never shrink)
        merged['students'] = _merge_students_preserve_active(
            local_data.get('students', []),
            peer_data.get('students', [])
        )
        merged['scores'] = _merge_scores_superset(
            local_data.get('scores', []),
            peer_data.get('scores', [])
        )
        merged['attendance'] = _merge_attendance_superset(local_data, peer_data)
        merged['appeals'] = _merge_appeals_superset(
            local_data.get('appeals', []),
            peer_data.get('appeals', [])
        )
        
        if peer_stamp > local_stamp:
            merged['server_updated_at'] = peer_data.get('server_updated_at')
        
        _save_offline_data(merged)  # ← Saves merged, preserves local data!
        _broadcast_sync_event(merged.get('server_updated_at'), source='bg-peer-pull')
```

**Key Changes**:
✅ Use `_merge_students_preserve_active()` instead of overwrite
✅ Use `_merge_scores_superset()` to preserve all scores
✅ Use `_merge_attendance_superset()` for attendance
✅ Merge appeals safely
✅ Only update timestamp if peer is genuinely newer
✅ Added logging to track preserved students

---

## 📊 How Merge Works

### Student Merge Example
```
Local:  [EA24A01, EA24A02, EA24C99(NEW)]
Peer:   [EA24A01, EA24A02]

Merge Process:
1. Index both lists by roll number
2. For each student in both: merge timestamps
3. For students only in local: ADD them (don't delete!)
4. For students only in peer: ADD them (superset)

Result: [EA24A01, EA24A02, EA24C99(NEW)] ✓ All preserved
```

### Score Merge Example
```
Local scores:  [EA24A01: 10pts, EA24A02: 5pts, EA24C99: 3pts(NEW)]
Peer scores:   [EA24A01: 10pts, EA24A02: 5pts]

Merge:
- EA24A01: 10pts appears in both → keep
- EA24A02: 5pts appears in both → keep
- EA24C99: 3pts only in local → ADD (don't delete!)

Result: [10, 5, 3] ✓ All preserved, no shrinking
```

---

## 🧪 Test Scenario

**Before Fix**:
```
Add student → Works ✓ (5 seconds)
         → Disappears ✗ (30 seconds later)
```

**After Fix**:
```
Add student → Works ✓ (5 seconds)
         → Still there ✓ (30 seconds later)
         → Still there ✓ (60 seconds later)
         → Synced to all devices ✓
```

---

## 🔒 Safety Improvements

### What's Protected Now

✅ **Newly added students**: Preserved during peer sync
✅ **Scores**: Superset merge ensures no data loss
✅ **Attendance**: Merged, not overwritten
✅ **Appeals**: Merged, not overwritten
✅ **Timestamps**: Only updated when peer is genuinely newer

### What Still Works

✅ **Valid conflicts**: Still resolved via version numbers
✅ **Shrink detection**: Still prevents data corruption
✅ **Peer push**: Still pushes when local is newer
✅ **Master mode**: Still works as authoritative
✅ **Background sync**: Still runs every 30 seconds

---

## 📋 Deployment Checklist

- [x] **Fixed**: Background peer sync now uses merge instead of overwrite
- [x] **Added**: Logging for preserved students
- [x] **Tested**: Merge logic works correctly
- [ ] Deploy to server
- [ ] Monitor logs for `[BgSync] PRESERVED` entries
- [ ] Test with multiple devices
- [ ] Verify students persist across 30s sync cycles

---

## 🔍 How to Verify the Fix

### In Server Logs
```bash
tail -f instance/logs/system.log | grep "BgSync"
```

Expected output:
```
[BgSync] Merged & pulled newer snapshot from http://peer:5000 
  (local: 3 students, peer: 2 students, result: 3 students, stamp=2026-04-04T12:00:25Z)
[BgSync] PRESERVED 1 locally-added students during peer pull
```

### Manual Test
1. Add new student "Test Student"
2. Wait 30+ seconds
3. Check if student still appears
4. Check server logs for `PRESERVED` entries

**Pass Criteria**:
- Student visible after 30 seconds ✓
- Log shows `PRESERVED` message ✓
- No data loss in scores/attendance ✓
- Other devices also see the student ✓

---

## 📝 Code Review Notes

**What Changed**:
- Lines 1201-1237: Peer pull now merges instead of overwrites
- Added merge calls for: students, scores, attendance, appeals
- Added logging for preserved student count
- Timestamp handling improved

**What Stayed the Same**:
- Shrink detection still works
- Peer push logic unchanged
- Master mode behavior unchanged
- SSE broadcasts still work

**No Breaking Changes**:
- API endpoints unchanged
- Client behavior unchanged
- Database schema unchanged

---

## 🎯 Impact

### Users
- Students won't disappear anymore
- Data is safer during sync
- Multi-device sync works better

### System
- More robust sync algorithm
- Better merge semantics
- Clearer logging for debugging

### Deployment
- Drop-in fix (no breaking changes)
- No database migrations needed
- Immediate protection for new students

---

## 🔗 Related Functions

```
_merge_students_preserve_active()    ← Preserves all students
_merge_scores_superset()             ← Preserves all scores  
_merge_attendance_superset()         ← Preserves all attendance
_merge_appeals_superset()            ← Preserves all appeals
_is_suspicious_student_shrink()      ← Still prevents data corruption
_do_peer_sync_cycle()                ← Fixed: now uses merge
```

---

## ✨ Summary

**Bug**: Students added locally were being deleted by background peer sync
**Cause**: Overwrite instead of merge (line 1205)
**Fix**: Use superset merge to preserve all data
**Risk**: None (backward compatible)
**Impact**: All students preserved during sync

🎉 **Status**: ✅ **FIXED**

