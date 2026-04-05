# Teacher Change Synchronization Test Plan

## Overview
This document provides a comprehensive testing guide to verify that teacher changes (scores, attendance, appeals) reach the server and are propagated to other devices.

---

## Architecture Summary

### Data Flow

```
Teacher Device 1 (makes changes)
    ↓
Client calls pushToServer() → POST /offline-data
    ↓
Server (_filter_teacher_payload_to_edit_window)
    ├─ Validates teacher credentials
    ├─ Filters changes to edit window (today ± N days)
    ├─ Merges scores/attendance/appeals/etc.
    ├─ Saves to offline_scoreboard_data.json
    └─ Broadcasts sync event
    ↓
Server forwards patch to peers (if replicated mode)
    ↓
Teacher Device 2 (receives update via SSE or pull)
    ├─ Receives sync event → /offline-events
    └─ Pulls latest data → GET /offline-data
```

### Key Files Involved
- **Client**: `/app/static/offline_scoreboard.html` (lines 18568+)
- **Server Endpoint**: `/app/routes/scoreboard.py` lines 5333-5597 (`@points_bp.route('/offline-data')`)
- **Teacher Merge Logic**: `/app/routes/scoreboard.py` lines 2142-2347 (`_merge_teacher_scores()`, `_filter_teacher_payload_to_edit_window()`)
- **Data Storage**: `instance/offline_scoreboard_data.json`

---

## Test Scenarios

### Scenario 1: Single Teacher Makes Score Change
**Goal**: Verify teacher changes save on server

#### Setup
1. Start server: `python run.py`
2. Login as Teacher (username: "Teacher", password from env)
3. Navigate to Scoreboard view

#### Test Steps
1. Select a student and award points (e.g., 5 points)
2. Verify the score shows locally
3. Check browser DevTools → Network tab
4. Look for POST request to `/offline-data`
5. **Verify response**: `{"success": true, "updated_at": "..."}` 

#### Verification
- [ ] POST request sent with `200 OK` response
- [ ] Server timestamp returned in response
- [ ] Change appears in browser DevTools (Network → Response)

---

### Scenario 2: Two Teacher Devices - Verify Sync
**Goal**: Verify changes on Device 1 appear on Device 2

#### Setup
1. Open Device 1: Teacher logged in, at Scoreboard view
2. Open Device 2: Teacher logged in, at Scoreboard view
   - Both devices should show same student data initially

#### Test Steps
1. **On Device 1**: Award 5 points to Student A
2. **Verify on Device 1**: Change appears locally
3. **Check Network tab (Device 1)**: POST /offline-data succeeds
4. **On Device 2**: 
   - Open browser DevTools → Console
   - Run: `console.log(JSON.stringify(db.getData().scores.filter(s => s.student_id === 'EA24A01'), null, 2))`
   - Note the current points for Student A
5. **Trigger Device 2 sync**:
   - Option A: Wait ~3 minutes for automatic sync cycle
   - Option B: Press F5 (refresh) to pull latest
   - Option C: Check browser DevTools → Console for SSE events

#### Verification
- [ ] Device 1 POST request succeeds
- [ ] Device 2 receives sync event (SSE) OR pulls fresh data
- [ ] Student A's points match on both devices
- [ ] Timestamp matches (`updated_at`)

---

### Scenario 3: Attendance Change by Teacher
**Goal**: Verify attendance records sync

#### Test Steps
1. **On Device 1 (Teacher)**: 
   - Mark Student B as "Absent" or "Late"
   - Check DevTools Network → verify POST to `/offline-data`
   - Response should include merged `attendance` array
   
2. **On Device 2 (Teacher)**:
   - Refresh page (F5) or wait for SSE update
   - Navigate to Attendance view
   - Verify Student B shows correct status

#### Verification
- [ ] POST includes `attendance` array in payload
- [ ] Server response merges attendance records
- [ ] Device 2 shows updated attendance
- [ ] Server logs show `[TEACHER SYNC] Attendance merged` (check `instance/logs/`)

---

### Scenario 4: Edit Window Validation
**Goal**: Verify teachers can ONLY edit within allowed time window

#### Test Steps
1. **On Device 1 (Teacher)**:
   - Check current date/time
   - Try to score changes for dates outside edit window (e.g., 30 days ago)
   - Submit changes

2. **Server-side check**:
   - Function `_filter_teacher_payload_to_edit_window()` (line 2285) should filter out-of-window changes
   - Old dates should NOT appear in `merged['scores']`

#### Verification
- [ ] Changes within window saved successfully
- [ ] Changes outside window filtered out by server
- [ ] Server logs show filtering action

---

### Scenario 5: Conflict Resolution
**Goal**: Verify version conflict handling

#### Test Steps
1. **Simulate conflict**:
   - Device 1: Make a change but DON'T sync
   - Server: Update data (e.g., via admin push)
   - Device 1: Try to sync now (base_version mismatch)

2. **Observe behavior**:
   - Expected: POST gets `409` Conflict response
   - Client should auto-retry: pull fresh data, re-sync

#### Verification
- [ ] Client receives `409` response with correct error code
- [ ] Client automatically pulls fresh data
- [ ] Client requeues sync after conflict resolution
- [ ] Final state is consistent across devices

---

## Manual Testing Checklist

### Before Testing
- [ ] Server is running (`python run.py`)
- [ ] Teacher credentials work (login as "Teacher")
- [ ] Database is healthy (`instance/offline_scoreboard_data.json` exists)
- [ ] Optional: 2+ devices available for cross-device testing

### During Testing
- [ ] Open DevTools (F12) on each device
  - Console tab: verify no JS errors
  - Network tab: watch for POST/GET to `/offline-data`
  - Storage → LocalStorage: verify `lastSyncTime` updates
  - Network → Headers: verify `Content-Type: application/json`

### Assertions
- [ ] Teacher login succeeds
- [ ] POST `/offline-data` response is `200 OK`
- [ ] Response JSON includes `updated_at` timestamp
- [ ] Server timestamp is newer than client timestamp
- [ ] No `403` or `401` errors (auth success)
- [ ] No version conflict errors (unless intentional test)
- [ ] SSE stream active (DevTools → Network → offline-events → Response tab shows stream data)
- [ ] Changes appear on other devices within 3 minutes

---

## Server-Side Verification

### Check Logs
```bash
# View last sync operations
tail -f instance/logs/system.log | grep "TEACHER SYNC"

# Check for any errors
tail -f instance/logs/system.log | grep -i "error\|failed"
```

### Check Stored Data
```bash
# Verify data saved to server
python -c "
import json
with open('instance/offline_scoreboard_data.json') as f:
    data = json.load(f)
    print(f'Students: {len(data.get(\"students\", []))}')
    print(f'Scores: {len(data.get(\"scores\", []))}')
    print(f'Attendance: {len(data.get(\"attendance\", []))}')
    print(f'Last updated: {data.get(\"server_updated_at\")}')"
```

### Check Activity Log
```bash
python -c "
import json
with open('instance/offline_scoreboard_data.json') as f:
    data = json.load(f)
    logs = data.get('activity_log', [])
    teacher_logs = [l for l in logs if 'Teacher' in str(l.get('actor', ''))]
    for log in teacher_logs[-5:]:
        print(f'{log.get(\"timestamp\")}: {log.get(\"action\")}')"
```

---

## Debugging Guide

### Issue: Teacher changes don't reach server

**Check 1: Authentication**
```javascript
// In browser console
console.log(document.cookie); // Should have session cookie
```

**Check 2: Network Request**
- DevTools → Network tab
- Filter for `offline-data`
- Check request headers: `Content-Type: application/json`
- Check request body: Should include `data` object with changes
- Check response status: Should be `200 OK`

**Check 3: Server Validation**
- Line 5339-5340: Check if teacher is authenticated
- Line 5497: Teacher filter window applied
- Line 5524: Teacher scores merged

### Issue: Other devices don't see changes

**Check 1: SSE Connection**
```javascript
// In browser console
console.log(window.syncEventSource); // Should exist
console.log(window.syncEventSource.readyState); // 0=connecting, 1=open
```

**Check 2: Pull Logic**
- Automatic pull every ~3 minutes (if enabled)
- Or manual pull via F5 refresh
- DevTools → Network tab → filter for `offline-data` GET requests

**Check 3: Data Merging**
- Check if `_merge_teacher_scores()` handles the specific data type
- Review merge logic for potential data loss

### Issue: Version Conflict (`409` error)

**Resolution**:
1. Check server timestamp vs client timestamp
2. Ensure only one device pushes at a time
3. Let client auto-retry (pulls fresh data first)
4. Check server logs for conflict reason

---

## Test Data Expectations

### Teacher Can Modify (Edit Window)
- Scores (recordedBy=teacher)
- Attendance records
- Appeals (own appeals only)
- Resource requests (team)
- Notification history
- Election teacher votes
- Pending CR requests

### Teacher Cannot Modify (Protected)
- Student roster (via direct scores)
- Leadership posts (readonly/approval-only)
- Class reps (readonly/approval-only)
- Parties (readonly)
- Post holder history (readonly)

---

## References

### Key Code Sections
1. **Teacher filter**: `_filter_teacher_payload_to_edit_window()` (line 2285)
2. **Teacher merge**: `_merge_teacher_scores()` (line 2142)
3. **Server endpoint**: `@points_bp.route('/offline-data')` (line 5333)
4. **Teacher sync block**: Lines 5496-5597
5. **Client push**: `pushToServer()` (line 18568)

### Environment Variables
- `TEACHER_PASSWORD`: Teacher login password
- `EA_MASTER_MODE=1`: Enable peer replication mode
- `SYNC_PEERS`: Comma-separated list of peer URLs
- `SYNC_SHARED_KEY`: Secret for peer authentication

---

## Success Criteria

✅ **Teacher changes reach server**: POST succeeds, data in `offline_scoreboard_data.json`
✅ **Changes persist across restarts**: Data remains after server restart
✅ **Multiple devices sync**: Changes on Device 1 appear on Device 2 within 3 min
✅ **Edit window enforced**: Out-of-window changes filtered by server
✅ **No data corruption**: Roster/protected tables never shrink
✅ **Conflicts resolved**: 409 errors handled gracefully
✅ **Audit trail**: Changes logged in activity_log

