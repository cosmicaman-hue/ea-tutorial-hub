# Project EA — Architecture & Recent Fixes Reference

> **Purpose:** Give any AI agent or developer a fast, accurate picture of the
> system architecture, the fixes applied on 2026-06-24, and the reasoning
> behind decisions made (and not made).

---

## 1. System Overview

Flask app hosted on **Cloudflare** with `gunicorn` (1 worker, 1 thread).
Primary data store is a **JSON file on disk** (`offline_scoreboard_data.json`,
~13 MB, 12k+ score rows). SQLAlchemy models exist but are vestigial for
scoreboard operations — the JSON file is the source of truth.

### Entry Points
| File | Role |
|---|---|
| `wsgi.py` / `app.py` | Gunicorn entry; calls `initialize_runtime()` |
| `run.py` | Dev entry; runtime bootstrap |
| `app/__init__.py` | App factory, extension init, JSON→DB sync, blueprint registration |

### Key Directories
```
app/
├── config/
│   ├── constants.py          # Generic schema/validation constants
│   └── seed_data.json        # FEB26 seed (moved here from scoreboard.py)
├── models/                   # SQLAlchemy models (vestigial for scoreboard)
├── routes/
│   ├── scoreboard.py         # 10.5k lines — main scoreboard logic (monolith)
│   ├── auth.py               # Authentication
│   ├── notebook.py           # Notebook (uses SafeFileWriter for data writes)
│   ├── veto_api.py           # VETO system API
│   └── star_validation.py    # Star validation API
├── static/
│   └── offline_scoreboard.html  # ~42k-line single-file SPA (all frontend)
└── utils/
    ├── data_paths.py         # Path resolution + mtime-cached JSON loader
    ├── file_operations.py    # FileLock, SafeFileWriter/Reader, AtomicFileOperation
    ├── helpers.py            # Shared pure functions (safe_int, norm_roll, etc.)
    ├── score_balance.py      # Star/VETO balance calculations
    ├── student_roster.py     # Active-roster visibility checks
    ├── veto_manager_unified.py  # VETO balance manager (uses SafeFileWriter)
    ├── secrets_manager.py    # Encrypted credential storage
    ├── logger.py             # Structured JSON logging
    ├── error_handler.py      # Centralized error handling
    ├── syllabus_helpers.py   # Syllabus merge helpers
    └── star_calculator.py    # StarCalculator class (delegates to score_balance)
```

---

## 2. Data Flow

```
Client (offline_scoreboard.html SPA)
  ↓ GET /scoreboard/offline-data
  ↓ POST /scoreboard/offline-data (sync push)
Flask (scoreboard.py)
  ↓ _load_offline_data()  →  data_paths.load_json_data_cached()
  ↓                          (mtime+size cache, thread-safe)
  ↓ _save_offline_data()  →  _atomic_write_json()  (FileLock + temp+rename)
  ↓                          _prime_data_cache()    (post-write cache priming)
  ↓                          _gist_push_snapshot_async()  (optional GitHub Gist)
Disk: offline_scoreboard_data.json
```

### Cache Layers
1. **Data cache** (`data_paths.py`): parsed dict cached by `(path, mtime_ns, size)`.
   Thread-safe via `_data_cache_lock`. Callers must treat returned dict as
   **read-only** — deep-copy before mutating.
2. **Serialized-response cache** (`data_paths.py`): pre-serialized bytes for
   `GET /offline-data` admin responses. Invalidated on any data change.

### Recovery Fallback Chain
`_load_offline_data()` tries in order:
1. Main JSON file (via cache)
2. Latest backup in `offline_scoreboard_backups/`
3. Hourly immutable backup
4. GitHub Gist snapshot
5. Hardcoded `FEB26_SEED` (now loaded from `app/config/seed_data.json`)

### Sync Mechanism
- **Delta sync**: `?since=server_updated_at` — server returns only new scores
- **Full sync**: when local data is corrupt/empty
- **Optimistic concurrency**: `server_version` (monotonic int) on every payload
- **Peer replication**: background thread when `EA_MASTER_MODE=1` + `SYNC_PEERS` set
- **SSE**: real-time push to connected clients

---

## 3. Fixes Applied (2026-06-24)

### 3.1 File Locking on Main Data Writes
**File:** `app/routes/scoreboard.py` — `_atomic_write_json()`

**Before:** Raw `tempfile.mkstemp()` + `os.replace()` with no lock. Concurrent
writes (peer sync + user edits) could interleave and corrupt the 13 MB JSON.

**After:** Wraps the temp-file + rename in a **per-file** `FileLock` (30s timeout).
Lock file naming: `.{basename}.lock` in the same directory — matches
`SafeFileWriter`/`SafeFileReader` convention so all read/write paths mutually
exclude correctly.

**Bug caught during review:** Initial version used a single hardcoded
`.offline_scoreboard_data.json.lock` for all 6 callers (main data, public
scores, restore meta, backups, safety restores). Fixed to per-file
(`.{os.path.basename(path)}.lock`) to prevent cross-file contention and
nested-lock deadlock.

### 3.2 Stale-Lock Reclamation
**File:** `app/utils/file_operations.py` — `FileLock` class

**Before:** If a process crashed mid-write, the orphaned `.lock` file blocked
all subsequent writes indefinitely (30s timeout → `TimeoutError`).

**After:** `FileLock.__init__` accepts `stale_after=60` (seconds). On
`FileExistsError`, `_reclaim_if_stale()` checks the lock file's mtime; if
older than 60s, it's unlinked and the next `os.open(O_CREAT|O_EXCL)` succeeds.
60s is far longer than any legitimate JSON write, so healthy holders are
never disturbed. Cross-platform (age-based, no PID liveness check needed).

**Verified:**
- Stale lock (>120s old) → reclaimed ✓
- Fresh lock (<1s old) → correctly blocks (acquire returns False) ✓

### 3.3 FEB26_SEED Externalized
**Before:** 110 lines of `json.loads(r'''...''')` inline in `scoreboard.py`.

**After:** `app/config/seed_data.json` — loaded once at module init via
`open()` + `json.load()`. Same data, same structure.

### 3.4 Shared Utility Functions
**New file:** `app/utils/helpers.py`

Consolidates `safe_int`, `safe_float`, `norm_roll`, `month_key`, `parse_stamp`,
`name_key` — previously duplicated across `student_roster.py`, `score_balance.py`,
and `scoreboard.py`.

**Updated:**
- `student_roster.py` — removed 3 dup functions, imports from `helpers.py`
- `score_balance.py` — removed 3 dup functions + `import re`, imports from `helpers.py`

**Not migrated:** `scoreboard.py`'s local copies (`_safe_int`, `_safe_float`,
`_roll_key`, `_name_key`, `_parse_stamp`, `_parse_int_safe`, `_parse_float_safe`).
They're functionally identical; migrating hundreds of call sites in a 10k-line
file is poor risk/reward under a data-integrity mandate.

### 3.5 Static Directory Cleanup
7 backup files (~10 MB) moved from `app/static/` to `backups/static_backups/`.
These were being served by Flask's static handler unnecessarily.

---

## 4. Deliberately NOT Changed (with reasoning)

| Item | Why Left Alone |
|---|---|
| `DEFAULT_PARTIES` / `DEFAULT_LEADERSHIP` duplication | Not true duplicates — `constants.py` has generic schema (parties with `name`, leadership with `vetoQuota`/`tenureMonths`/`holder=None`); `scoreboard.py` has operational seed (verbose post titles, real holder names). Merging would change disk-written data shape. |
| Monolithic `scoreboard.py` (10.5k lines) | Splitting into blueprints is a large refactor — unsafe for incremental reliability pass. |
| Dual data architecture (JSON file vs SQLAlchemy) | Architectural; no safe incremental fix. |
| 42k-line single-file SPA | Out of scope for backend reliability work. |
| GitHub Gist coupling in save path | Functional; left as-is. |

---

## 5. Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `EA_STORAGE_ROOT` | Override storage root directory | Falls back to Flask instance_path |
| `EA_MIN_SAFE_STUDENT_ROSTER` | Minimum healthy roster count | 25 |
| `EA_MASTER_MODE` | Enable master replication mode | unset |
| `EA_RESTORE_LOCK` | Lock restores | unset |
| `EA_TIMEZONE` | Server timezone | `Asia/Kolkata` |
| `GITHUB_GIST_TOKEN` | Gist snapshot push | unset |
| `GITHUB_GIST_ID` | Gist ID | unset |
| `GITHUB_GIST_FILENAME` | Gist filename | unset |
| `EA_INIT_ON_BOOT` | Run `initialize_runtime()` on boot | unset |

---

## 6. Key Constants

| Constant | Value | Location |
|---|---|---|
| `_SEED_STAMP` | `2026-02-26T00:00:00+00:00` | `scoreboard.py` |
| `HISTORY_CUTOFF` | `2026-02` | `scoreboard.py` |
| `MIN_SAFE_STUDENT_ROSTER` | 25 | client + server |
| Lock stale threshold | 60s | `file_operations.py` |
| Lock timeout | 30s | `file_operations.py` + `scoreboard.py` |

---

## 7. Verification Checklist (post-fix)

- [x] `helpers.py` — all functions return correct values
- [x] `student_roster.py` — imports and functions work
- [x] `score_balance.py` — imports and functions work
- [x] `FEB26_SEED` — loads from JSON: 45 students, 33 scores, 6 parties, 14 posts
- [x] `_atomic_write_json` — per-file locking verified with two concurrent paths
- [x] Stale lock reclamation — orphaned lock reclaimed; fresh lock correctly blocks
- [x] Full app boot — 104 routes registered, no errors
- [x] Data integrity — 96 students, 12,206 scores, server_version 4076 (intact)

---

## 8. Known Remaining Issues (for future work)

1. **`scoreboard.py` local util duplicates** — `_safe_int` etc. still defined
   locally; could import from `helpers.py` but touches hundreds of call sites.
2. **`FileLock` has no re-entrancy** — a thread holding a lock and calling
   another function that acquires the same lock will deadlock. Not currently
   triggered but worth documenting.
3. **Client-side `addScore()` uses `Date.now()` for IDs** — millisecond
   collision risk. Server-side merge has `ensureUniqueScoreIds()` but initial
   add doesn't.
4. **`preserveHistoricalMonthSnapshots` fragility** — any new startup repair
   calling `saveData()` without `allowHistoricalWrite:true` can re-trigger
   locked-month data loss (mitigated by superset merge fix, not eliminated).
5. **`TEMP_DISABLE_AUTO_SYNC_LOOPS = true`** — auto-sync permanently disabled
   in the SPA; realtime sync and polling are gated behind this flag.
