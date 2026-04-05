# Teacher Sync - Quick Reference Guide

## TL;DR - Run Tests Now

### Option 1: Automated Test (Recommended)
```bash
# In project root
python test_teacher_sync.py --server http://localhost:5000
```

Expected output:
```
✓ Server is reachable
✓ Teacher login succeeds
✓ GET /offline-data succeeds
✓ POST /offline-data succeeds
✓ Server returned timestamp
✓ Data persisted on server
✓ Teacher merge logic works
✓ Edit window filters old scores
✓ SSE endpoint available

Results: 8/8 tests passed
```

### Option 2: Manual Verification (5 minutes)

1. **Login as Teacher**
   - Username: `Teacher`
   - Password: from `TEACHER_PASSWORD` env var (default: `ChangeTeacherPass123!`)

2. **Make a Change**
   - Award points to a student
   - OR mark attendance
   - OR create an appeal

3. **Verify in DevTools**
   - Open DevTools (F12)
   - Network tab → Filter: `offline-data`
   - Should see `POST` request with status `200 OK`
   - Response body includes: `"success": true, "updated_at": "2026-04-04T..."`

4. **Verify on Another Device** (Optional)
   - Open same app in another browser/device
   - Login as Teacher
   - Refresh page (F5)
   - Changes should appear within ~3 minutes

---

## Data Flow at a Glance

```
┌─────────────────────────────────────┐
│  Teacher Client (Device 1)          │
│  • Makes score/attendance changes   │
│  • Calls: pushToServer()            │
└────────────────────┬────────────────┘
                     │ POST /offline-data
                     ▼
┌─────────────────────────────────────┐
│  Server                             │
│  1. Validate teacher credentials    │
│  2. Filter to edit window (N days)  │
│  3. Merge with existing data        │
│  4. Save to disk/database           │
│  5. Broadcast sync event (SSE)      │
│  6. Forward to peer servers         │
└────────┬──────────────────┬─────────┘
         │                  │
    SAVED DATA          SSE BROADCAST
         │                  │
         ▼                  ▼
┌──────────────┐      ┌──────────────┐
│ Disk Storage │      │ Teacher      │
│ (json file)  │      │ Device 2     │
└──────────────┘      │ Receives     │
                      │ sync event   │
                      │ Pulls fresh  │
                      │ data         │
                      └──────────────┘
```

---

## Key Verification Points

### ✓ Changes Reach Server
- POST request to `/offline-data` returns `200 OK`
- Response includes `updated_at` timestamp
- Data visible in `instance/offline_scoreboard_data.json`

### ✓ Changes Sync to Other Devices
- Device 2 receives SSE sync event within seconds
- Device 2 pulls fresh data automatically
- Or manual refresh (F5) shows changes

### ✓ Edit Window Enforced
- Teachers can only modify scores in window (today ± N days)
- Old scores are filtered out by server
- Check `_filter_teacher_payload_to_edit_window()` in code

### ✓ No Data Loss
- Merge logic preserves existing data
- Protected tables (leadership, class reps) never shrink
- Version conflicts resolved automatically

---

## What Gets Synced?

### ✓ Can Modify (Edit Window)
- ✓ Scores (with `recordedBy: "teacher"`)
- ✓ Attendance (present/absent/late)
- ✓ Appeals (own appeals only)
- ✓ Resource requests
- ✓ Notifications
- ✓ Election votes (teacher votes)

### ✗ Cannot Modify
- ✗ Student roster (protected)
- ✗ Leadership posts (admin only)
- ✗ Class reps (admin only)
- ✗ Parties (readonly)
- ✗ Post holder history (readonly)

---

## Troubleshooting

### Problem: POST returns 403/401
**Solution**: Teacher session expired
- Logout and login again
- Check browser cookies: `F12 → Storage → Cookies`

### Problem: POST returns 409 (Conflict)
**Solution**: Server has newer data
- Expected! Client auto-handles this:
  1. Pulls fresh data
  2. Re-merges locally
  3. Re-syncs to server
- Check browser console: Should show "Server had newer data. Refreshed..."

### Problem: Changes on Device 1 don't appear on Device 2
**Solutions**:
- A. Wait 3 minutes for automatic sync cycle
- B. Manually refresh: F5 on Device 2
- C. Check network: Both devices must reach same server
- D. Check logs: `tail -f instance/logs/system.log`

### Problem: Old dates got saved (shouldn't happen)
**Cause**: Server-side edit window filter wasn't applied
**Check**: Server code line 2285 `_filter_teacher_payload_to_edit_window()`

### Problem: SSE not updating
**Check**:
```javascript
// In browser console
console.log(window.syncEventSource.readyState); // 1 = connected
// Should see sync events in Network tab
```

---

## Server Logs

### Check Recent Teacher Syncs
```bash
tail -f instance/logs/system.log | grep "TEACHER SYNC"
```

### Check Data File
```bash
python -c "
import json
with open('instance/offline_scoreboard_data.json') as f:
    data = json.load(f)
    print(f'Last updated: {data.get(\"server_updated_at\")}')
    print(f'Students: {len(data.get(\"students\", []))}')
    print(f'Scores: {len(data.get(\"scores\", []))}')
    print(f'Attendance: {len(data.get(\"attendance\", []))}')
"
```

### Check Activity Log (last 10 teacher actions)
```bash
python -c "
import json
with open('instance/offline_scoreboard_data.json') as f:
    data = json.load(f)
    logs = [l for l in data.get('activity_log', []) if 'Teacher' in str(l.get('actor', ''))]
    for log in logs[-10:]:
        print(f'{log.get(\"timestamp\")}: {log.get(\"action\")}')"
```

---

## Environment Variables

```bash
# Teacher credentials
TEACHER_PASSWORD=ChangeTeacherPass123!

# Optional: Enable peer sync
EA_MASTER_MODE=1
SYNC_PEERS=http://peer1:5000,http://peer2:5000
SYNC_SHARED_KEY=your-secret-key

# Optional: Enable rate limiting (LAN mode defaults to unlimited)
ENABLE_RATE_LIMITING=0

# Optional: Restore lock (prevents new syncs)
EA_RESTORE_LOCK=0
```

---

## Architecture Deep Dive

### Client Side (offline_scoreboard.html)
- Line 18568: `pushToServer()` - sends changes to server
- Handles 401/403: Auto-refreshes session and retries
- Handles 409: Auto-pulls fresh data and re-syncs
- Dedup: Uses `op_id` to prevent duplicate POSTs

### Server Side (app/routes/scoreboard.py)
- Line 5333: `@points_bp.route('/offline-data')` - main sync endpoint
- Line 5405-5414: Determines actor role (teacher/admin/student)
- Line 5496-5597: Teacher-specific merge logic
  - Line 5497: Filters to edit window
  - Line 5524: Merges scores (superset)
  - Line 5530: Merges attendance
  - Line 5526: Merges appeals
- Line 2285: `_filter_teacher_payload_to_edit_window()` - enforces edit window
- Line 2142: `_merge_teacher_scores()` - safe merge of scores

### Merge Strategy
- Superset merge: Keep all existing data, add new data
- Never shrink protected tables
- Preserve timestamps for conflict resolution
- Activity log appended for audit trail

---

## Success Checklist

- [ ] Run automated test: `python test_teacher_sync.py`
- [ ] All 8 tests pass
- [ ] Manual test: Teacher changes appear on server
- [ ] Manual test: Changes reach 2nd device within 3 min
- [ ] Log check: No errors in server logs
- [ ] Data check: No protected tables shrunk
- [ ] Edit window check: Old dates filtered out

---

## Questions?

Check these files for details:
- **Manual tests**: `TEST_TEACHER_SYNC.md`
- **Code flow**: `app/routes/scoreboard.py` (lines 5333-5597)
- **Merge logic**: `app/routes/scoreboard.py` (lines 2142-2347)
- **Client sync**: `app/static/offline_scoreboard.html` (lines 18568+)
