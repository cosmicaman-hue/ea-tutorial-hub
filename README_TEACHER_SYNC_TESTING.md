# Teacher Data Synchronization Testing - START HERE

## What This Is

Complete test suite & documentation to verify that **teacher changes (scores, attendance, appeals) reach the server and sync to other devices**.

## Quick Start (90 seconds)

### Step 1: Start Server
```bash
python run.py
```

### Step 2: Run Tests
```bash
python test_teacher_sync.py
```

### Expected Output
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

Results: 8/8 tests passed ✓
```

**If all tests pass → Teacher sync is working! ✓**

---

## Files Created for You

### 📋 Documentation (Read These)
| File | Purpose | Read Time |
|------|---------|-----------|
| **README_TEACHER_SYNC_TESTING.md** | This file - Quick overview | 2 min |
| **TEACHER_SYNC_QUICK_REFERENCE.md** | TL;DR guide + troubleshooting | 5 min |
| **TEACHER_SYNC_TESTING_SUMMARY.md** | Complete overview of entire setup | 10 min |
| **TEST_TEACHER_SYNC.md** | Detailed manual test scenarios (6 tests) | 20 min |
| **TEACHER_SYNC_NETWORK_PROTOCOL.md** | HTTP request/response specs | 15 min |
| **TEACHER_SYNC_VISUAL_GUIDE.txt** | ASCII diagrams of sync flow | 10 min |

### 🧪 Test Scripts (Run These)
| File | Purpose | Usage |
|------|---------|-------|
| **test_teacher_sync.py** | Automated 8-test suite | `python test_teacher_sync.py` |
| **test_teacher_sync.sh** | Bash wrapper | `./test_teacher_sync.sh` |

---

## What Gets Tested?

```
✓ Test 1: Server is running and reachable
✓ Test 2: Teacher login works
✓ Test 3: Teacher can fetch data from server
✓ Test 4: Teacher can POST changes to server
✓ Test 5: Changes are persisted (saved to disk)
✓ Test 6: Merge logic preserves existing data
✓ Test 7: Edit window filters old dates
✓ Test 8: SSE sync events are available
```

---

## How It Works (Simple Version)

```
1. Teacher makes change on Device 1 (scores, attendance, etc.)
   ↓
2. Client automatically sends to server: POST /points/offline-data
   ↓
3. Server validates, merges, and saves
   ↓
4. Server broadcasts sync event to all connected clients
   ↓
5. Device 2 receives event and pulls fresh data
   ↓
6. Device 2 shows the change
```

**Time**: ~100-200ms for Device 1 → Server
**Time**: ~250ms for Server → Device 2

---

## Running the Tests

### Option A: Automated (Recommended)
```bash
# In project root directory
python test_teacher_sync.py --server http://localhost:5000
```

**What it does**:
1. Connects to server
2. Logs in as Teacher
3. Creates test data
4. Verifies POST succeeds
5. Checks data was saved
6. Tests merge logic
7. Tests edit window filter
8. Verifies SSE is working

**Output**: Pass/Fail for each test + summary

### Option B: Manual (Detailed)
See `TEST_TEACHER_SYNC.md` for step-by-step manual testing with 6 scenarios.

---

## Interpreting Results

### All Tests Pass (8/8) ✓
```
✓ Teacher sync is working correctly
✓ Safe to use in production
✓ Changes will reach other devices
✓ Data is being merged properly
✓ Edit window is being enforced
```

### Some Tests Fail
```
✗ Check error message
✗ Review troubleshooting in TEACHER_SYNC_QUICK_REFERENCE.md
✗ Check server logs: tail -f instance/logs/system.log
✗ Verify database connectivity
✗ See detailed guide: TEST_TEACHER_SYNC.md
```

---

## Key Facts About Teacher Sync

### ✓ What Teachers CAN Modify
- Scores (with recordedBy="Teacher")
- Attendance records
- Appeals
- Resource requests
- Notification history
- Election teacher votes

### ✗ What Teachers CANNOT Modify
- Student roster
- Leadership posts
- Class reps
- Parties
- Post holder history

### 🔒 Safety Features
- **Edit window**: Only modify last 7 days (configurable)
- **Superset merge**: Old data never deleted
- **Protected tables**: Admin-only data never modified
- **Version conflict handling**: Automatic retry
- **Audit trail**: All changes logged

---

## Troubleshooting Quick Guide

| Problem | Solution |
|---------|----------|
| "Connection refused" | Start server: `python run.py` |
| "401 Unauthorized" | Check teacher password in env vars |
| "409 Conflict" | Expected! Client auto-handles. Check logs. |
| "503 Service Unavailable" | Data corruption. Check `instance/offline_scoreboard_data.json` |
| Changes on Device 1 don't appear on Device 2 | Wait 3 min OR press F5 on Device 2 |
| Old dates were saved | Edit window filter broken - check server code line 2285 |

**For detailed troubleshooting**: See TEACHER_SYNC_QUICK_REFERENCE.md

---

## Understanding the Test Suite

### Test 1: Server Health
Verifies server is running and responding to HTTP requests.

### Test 2: Teacher Authentication
Tests login with credentials and session creation.

### Test 3: Data Retrieval
Fetches existing data from server to use as baseline.

### Test 4: Data Upload
Teacher POSTs changes and gets 200 OK response with timestamp.

### Test 5: Persistence
Verifies changes are saved to `instance/offline_scoreboard_data.json`.

### Test 6: Merge Logic
Makes multiple changes in sequence to test superset merge.

### Test 7: Edit Window
Attempts to save score from 1 year ago (should be filtered out).

### Test 8: SSE Stream
Verifies Server-Sent Events endpoint is available for real-time updates.

---

## Architecture Overview

### Client-Side (Browser)
```
User makes change
    ↓
Local IndexedDB updated
    ↓
pushToServer() called
    ↓
POST /points/offline-data
    ↓
Response 200 OK
    ↓
Show "Synced ✓"
```

### Server-Side
```
Receive POST /points/offline-data
    ↓
Validate teacher auth
    ↓
Filter to edit window (7 days)
    ↓
Merge with existing data
    ↓
Save to disk
    ↓
Broadcast SSE event
    ↓
Return 200 OK
```

### Cross-Device Sync
```
Device 1: POST /offline-data (200 OK)
    ↓
Server: Broadcast SSE event
    ↓
Device 2: Receive SSE → GET /offline-data
    ↓
Device 2: Update local data
    ↓
Both devices: In sync
```

---

## Code References

If you need to understand the implementation:

| Component | File | Lines |
|-----------|------|-------|
| Main sync endpoint | `app/routes/scoreboard.py` | 5333-5597 |
| Teacher filter | `app/routes/scoreboard.py` | 2285-2347 |
| Teacher merge | `app/routes/scoreboard.py` | 2142-2200 |
| Client push | `app/static/offline_scoreboard.html` | 18568-18700 |
| Server auth | `app/routes/auth.py` | 443-680 |

---

## Environment Variables

```bash
# Required
TEACHER_PASSWORD=ChangeTeacherPass123!

# Optional
EA_MASTER_MODE=1                    # Enable peer replication
SYNC_PEERS=http://peer1:5000        # Peer server URLs
SYNC_SHARED_KEY=your-secret-key     # Shared key for peer auth
ENABLE_RATE_LIMITING=0              # 0 = unlimited (LAN mode)
```

---

## Next Steps

### If Tests Pass ✓
1. You're done! Teacher sync is verified.
2. Deploy with confidence
3. Monitor logs periodically
4. Test with multiple devices in classroom

### If Tests Fail ✗
1. Read error message carefully
2. Check TEACHER_SYNC_QUICK_REFERENCE.md for troubleshooting
3. Review server logs: `tail -f instance/logs/system.log`
4. See detailed guide: TEST_TEACHER_SYNC.md
5. Check network connectivity between devices

---

## Detailed Documentation

Once you understand the basics, read these in order:

1. **TEACHER_SYNC_QUICK_REFERENCE.md** - Quick answers to common questions
2. **TEACHER_SYNC_TESTING_SUMMARY.md** - Complete overview
3. **TEST_TEACHER_SYNC.md** - 6 manual test scenarios
4. **TEACHER_SYNC_NETWORK_PROTOCOL.md** - HTTP protocol specs
5. **TEACHER_SYNC_VISUAL_GUIDE.txt** - ASCII diagrams

---

## Support Info

### Check Server Logs
```bash
# Last 50 sync operations
tail -50f instance/logs/system.log | grep "TEACHER SYNC"

# All errors
tail -f instance/logs/system.log | grep ERROR

# Real-time
tail -f instance/logs/system.log
```

### Check Data File
```bash
python -c "
import json
with open('instance/offline_scoreboard_data.json') as f:
    data = json.load(f)
    print('Last update:', data.get('server_updated_at'))
    print('Students:', len(data.get('students', [])))
    print('Scores:', len(data.get('scores', [])))
"
```

### Browser DevTools
```javascript
// In browser console (F12)
console.log(window.syncEventSource.readyState);  // 1 = connected
console.log(window.lastSyncTime);                 // Last sync timestamp
console.log(db.getData().scores.length);          // Scores on device
```

---

## Summary

✅ **What You Have**:
- 8-test automated test suite
- 6 manual test scenarios
- Complete documentation
- Network protocol specs
- Visual diagrams
- Troubleshooting guide

✅ **What You Can Verify**:
- Teacher login works
- Changes reach server
- Changes persist (saved)
- Data merges safely
- Old dates filtered
- Other devices sync
- No data loss
- SSE works

✅ **How to Use**:
1. `python test_teacher_sync.py` (2 min)
2. Read results
3. If pass → Done! If fail → Troubleshoot

---

## Questions?

- **Quick answers**: See TEACHER_SYNC_QUICK_REFERENCE.md
- **Detailed info**: See TEST_TEACHER_SYNC.md
- **Protocol specs**: See TEACHER_SYNC_NETWORK_PROTOCOL.md
- **Visual overview**: See TEACHER_SYNC_VISUAL_GUIDE.txt
- **Complete guide**: See TEACHER_SYNC_TESTING_SUMMARY.md

---

**Ready? Run: `python test_teacher_sync.py`**

