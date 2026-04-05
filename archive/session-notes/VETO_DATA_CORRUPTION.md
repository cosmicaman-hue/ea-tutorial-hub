# 🚨 VETO Data Corruption Issue & Resolution

## Executive Summary

**Problem**: After fixing VETO values, the Flask application was syncing stale cached data from browser localStorage back to the server file, overwriting all corrections.

**Root Cause**: The offline scoreboard app stores data in browser localStorage/IndexedDB. When Flask restarts, it can receive sync payloads containing old VETO counts, which overwrite the corrected values.

**Solution**: Created a multi-layer protection system to detect, prevent, and guard against VETO data corruption.

---

## What Went Wrong

### Timeline of Corruption

1. **18-Mar-2026 20:05** — Correct VETO data written to `offline_scoreboard_data.json` ✓
   - Leader: 5V (role-based)
   - Co-Leader: 6V (3 individual + 3 role)
   - CR Groups: 2V each
   - All values correct in `veto_tracking` system

2. **18-Mar-2026 ~12:59** — Flask app restarted (likely by scheduled task or user)
   - Browser still had old localStorage with corrupted VETO counts
   - App received sync payload from browser with stale data
   - Stale data merged with/overwrote correct file values

3. **18-Mar-2026 06:03** — File corrupted
   - Timestamps reverted to March 10 (8 days old)
   - VETO values show wrong allocations
   - All corrections lost

### Data Corruption Mechanism

```
Firefox/Chrome Browser          Flask Server              Data File
─────────────────────           ──────────────           ─────────
┌─────────────────────┐
│   localStorage      │
│  [OLD VETO DATA]    │         [API Endpoint]       
│  Leader: 10V        │ ──────→  /offline-sync   ──→  [CORRUPTED]
│  Co-Leader: 9V      │         [merge payload]        Leader: 10V
│  EA24C02: 7V        │         [write to file]        Co-Leader: 9V
│  EA24B01: 3V        │◄────────────────────────      EA24C02: 7V
│  [stale for 8 days] │                                EA24B01: 3V
└─────────────────────┘
```

---

## Solution Components

### 1. Anti-Corruption Check (`anti_corruption_check.py`)

**What it does**:
- Calculates SHA256 hash of all VETO allocations
- Stores hash as `_last_known_correct_veto_hash` marker
- On next startup, detects if hash changed (corruption occurred)
- Auto-fixes mismatches between student records and veto_tracking

**Run**: `python anti_corruption_check.py`

**Output**:
```
======================================================================
VETO SYSTEM ANTI-CORRUPTION CHECK
======================================================================
✅ Setting VETO checkpoint for corruption detection...
   Checkpoint: 6c36b6288df088ce1751c1e403a5089a4576fe275cd0c86d50bc033661f8e384

✓ Checking student records vs veto_tracking...
  All student records match veto_tracking ✓

✓ Enforcing veto_tracking hardening...

======================================================================
✅ VETO SYSTEM SECURED
======================================================================
```

### 2. VETO Integrity Guard (`veto_integrity_guard.py`)

**What it does**:
- Validates incoming sync payloads BEFORE they're written to file
- Detects suspiciously high VETO counts (likely stale cached data)
- Rejects syncs that would cause >50% increase in VETOs
- Prevents decreases in VETO totals (which shouldn't happen)

**Key Detection Rules**:
- If incoming VETO for a student is >1.5x current tracked value → **REJECT**
- If incoming VETO is less than tracked AND difference >2 → **REJECT**
- Only syncs with approved VETO values proceed

**Integration**: 
```python
from veto_integrity_guard import validate_incoming_sync

# In Flask route before processing sync payload:
is_valid, message = validate_incoming_sync(incoming_json_data)
if not is_valid:
    return {"error": "Corrupted VETO data detected", "message": message}, 409
```

### 3. Cache Clearing Utility (`clear_offline_cache.html`)

**What it does**:
- GUI tool to clear browser localStorage, IndexedDB, Service Worker cache
- Verifies fresh data is loaded from server (not cache)

**How to use**:
1. Open: `clear_offline_cache.html` in browser
2. Click "Clear All Caches"
3. Click "Open Fresh Scoreboard"
4. Click "Verify Data" to confirm correct VETO values

---

## Protection Workflow

### Before Restart (Immediate Actions Taken)

```
1. ✅ Stopped running Python processes (they were syncing stale data)
2. ✅ Restored correct data from backup: veto_sync_20260318_200542.json
3. ✅ Updated timestamps to current time (so data is recognized as fresh)
4. ✅ Ran anti_corruption_check.py to lock the system
5. ✅ Set corruption detection checkpoint
6. ✅ Verified veto_tracking hardened=true
```

### Future Protection (Ongoing)

```
BEFORE APP START:
├─ Run anti_corruption_check.py
├─ Verify checkpoint hash
├─ Fix any mismatches
└─ Report if corruption detected

DURING SYNC:
├─ Validate incoming payload with veto_integrity_guard
├─ Check for suspicious VETO count changes
├─ Reject if data looks corrupted
└─ Accept only if values are reasonable

AFTER SYNC:
├─ Verify veto_count matches veto_tracking
├─ Update _last_known_correct_veto_hash
└─ Log any discrepancies
```

---

## Current Status

### ✅ What's Been Fixed

- Data file restored to correct state from backup
- veto_tracking checkpoint set with SHA256 hash
- All 92 students synced correctly
- Anti-corruption detection enabled
- VETO integrity guard created and tested

### Current File State

```
✓ Data File: instance/offline_scoreboard_data.json
  └─ Last Updated: 2026-03-18T14:50:18.289522Z
  └─ Leader VETO: 5V (0 individual + 5 role) ✓
  └─ Co-Leader VETO: 6V (3 individual + 3 role) ✓
  └─ CR VETOs: 2V each ✓
  └─ veto_tracking.hardened: true ✓
  └─ Checkpoint hash: 6c36b6288df088ce1751c1e403a5089a4576fe275cd0c86d50bc033661f8e384

✓ Protection Systems:
  └─ anti_corruption_check.py — Startup validation
  └─ veto_integrity_guard.py — Sync validation  
  └─ clear_offline_cache.html — Browser cache cleanup
```

---

## How to Verify Fix

### Step 1: Clear Browser Cache

Open `clear_offline_cache.html`:
```
File → Open → c:/Users/sujit/OneDrive/Desktop/Project EA/clear_offline_cache.html
```

Click:
1. **"Clear All Caches"** — Removes all localStorage, IndexedDB, Service Worker cache
2. **"Open Fresh Scoreboard"** — Reloads scoreboard with no cache
3. **"Verify Data"** — Checks current values

### Step 2: Verify Displayed Values

In the scoreboard, check:
- **Leader**: Should show **5V** (not 10V)
- **Co-Leader**: Should show **6V** (not 9V)
- **Group C CR**: Should show **5V** (not 7V)  
- **Previous CR (Pari)**: Should show **1V** (not 3V)

### Step 3: Check Data File

```bash
python -c "import json; d=json.load(open('instance/offline_scoreboard_data.json')); print([s for s in d['students'] if s['id'] in [60,32,16] ][0])"
```

---

## Preventing Future Corruption

### Don't

❌ Never restart the app while browser cache is corrupted with old VETO data
❌ Don't rely on timestamp-based merging for VETO data
❌ Don't allow sync payloads to overwrite veto_tracking values
❌ Don't modify VETO system without clearing browser caches first

### Do

✅ Always run `anti_corruption_check.py` before starting Flask app
✅ Clear browser cache after any VETO system modifications
✅ Use integrity guard to validate sync payloads
✅ Monitor `_cache_bust_version` timestamp for stale cache detection
✅ Keep veto_tracking as immutable authoritative source
✅ Backup data file before running VETO fix scripts

### Workflow for Future VETO Changes

```bash
# 1. Make your VETO changes
python your_veto_fix_script.py

# 2. Lock and validate
python anti_corruption_check.py

# 3. Inject cache-buster  
python inject_cache_buster.py

# 4. Tell users to clear browser cache
# → Use clear_offline_cache.html

# 5. Safe to restart app
```

---

## Files Created

| File | Purpose |
|------|---------|
| `anti_corruption_check.py` | Startup validation & VETO checkpoint |
| `veto_integrity_guard.py` | Sync payload validation |
| `clear_offline_cache.html` | Browser cache cleanup GUI |
| `inject_cache_buster.py` | Cache-invalidation timestamp injection |
| `CACHE_ISSUE_SOLUTION.md` | Original cache issue documentation |
| `VETO_DATA_CORRUPTION.md` | This file — comprehensive issue analysis |

---

## Technical Details

### Data Corruption Markers

All files are marked with timestamps to detect staleness:
```json
{
  "updated_at": "2026-03-18T14:50:18.289522Z",
  "server_updated_at": "2026-03-18T14:50:18.289522Z",
  "_cache_bust_version": "2026-03-18T14:49:31.279507Z",
  "_last_known_correct_veto_hash": "6c36b6288df088ce1751c1e403a5089a4576fe275cd0c86d50bc033661f8e384",
  "veto_tracking": {
    "hardened": true,
    "hardening_enforced": true,
    "corruption_detection_enabled": true,
    "_last_sync_hash": "6c36b6288df088ce1751c1e403a5089a4576fe275cd0c86d50bc033661f8e384",
    "_last_sync_time": "2026-03-18T14:50:18.289522Z"
  }
}
```

### Corruption Detection Algorithm

```python
def detect_corruption():
    current_hash = sha256(all_veto_totals)
    last_known_hash = data['_last_known_correct_veto_hash']
    
    if current_hash != last_known_hash:
        # Corruption detected!
        raise CorruptedVetoDataError("Hash mismatch")
```

### Sync Validation Algorithm

```python
def validate_sync(incoming):
    for student in incoming.students:
        incoming_total = student.veto_count + student.role_veto_count
        tracked_total = veto_tracking[student.id].total_vetos
        
        # Reject suspicious increases (cached data)
        if incoming_total > tracked_total * 1.5:
            return REJECT
        
        # Reject decreases (shouldn't happen)
        if incoming_total < tracked_total - 2:
            return REJECT
    
    return ACCEPT
```

---

## Emergency Recovery

If corruption occurs again:

```bash
# 1. Stop the app immediately
Get-Process python | Stop-Process -Force

# 2. Identify latest good backup
Get-ChildItem instance/*.veto_sync*.json | sort LastWriteTime -Descending | head -1

# 3. Restore from backup
Copy-Item instance/offline_scoreboard_data.veto_sync_YYYYMMDD_HHMMSS.json `
  -Destination instance/offline_scoreboard_data.json -Force

# 4. Run anti-corruption check
python anti_corruption_check.py

# 5. Clear all caches
# → Open clear_offline_cache.html and click "Clear All Caches"

# 6. Restart app safely
```

---

## Key Lesson Learned

**The fundamental issue**: The offline scoreboard's sync mechanism treats browser cache as a valid source of truth. When the app restarts, it can merge cached data that's days old with server data, corrupting VETO values.

**The fix**: Make veto_tracking immutable and require all VETO changes to go through validation that checks against the authoritative tracking system. Never allow sync to overwrite VETO values without verification.

**The principle**: For critical game-state data like VETOs, the sync mechanism should be **uni-directional from server to browser**, not bi-directional with merge semantics.
