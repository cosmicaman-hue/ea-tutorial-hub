# Utility Scripts

This directory contains **actively maintained** utility and maintenance scripts for the EA Tutorial Hub project.

> **Historical incident scripts** (one-off fixes, diagnostics) have been moved to `archive/incident-scripts/`.

## Active Scripts

### veto_manager.py
**Purpose**: Complete VETO system initialization and management

**Usage**:
```bash
python scripts/veto_manager.py
```

**What it does**:
1. Removes all VETOs from everyone
2. Grants individual VETOs to specific students (Ayush:1V, Arman:1V, etc.)
3. Adds role-grant VETOs to post-holders (LEADER:5RV, CO-LEADER:3RV, etc.)
4. Hardens the VETO system with immutable tracking
5. Tracks usage with automatic deduction from global counter

**When to use**:
- Initial VETO system setup
- After major roster changes
- To reset and reinitialize VETO allocations

---

### anti_corruption_check.py
**Purpose**: Verify data integrity and detect VETO corruption

**Usage**:
```bash
python scripts/anti_corruption_check.py
```

**What it does**:
- Validates JSON file structure
- Checks VETO data consistency between `veto_tracking` and `students[]`
- Detects corrupted records from stale browser sync
- Auto-fixes mismatches using `veto_tracking` as authority

**When to use**:
- After system crashes
- Before major operations
- Regular maintenance checks

---

### inject_cache_buster.py
**Purpose**: Inject cache-busting timestamp into data file

**Usage**:
```bash
python scripts/inject_cache_buster.py
```

**What it does**:
- Adds `_cache_bust_version` timestamp to the data file
- Forces browser localStorage invalidation on next page load

**When to use**:
- After deploying frontend changes
- When users report stale data

---

### rebuild_from_excel.py
**Purpose**: Full historical data rebuild from Excel source

**Usage**:
```bash
python scripts/rebuild_from_excel.py
```

**What it does**:
- Rebuilds the entire offline scoreboard data from the Excel tally sheet
- Maps historical months (Aug 2024–Jan 2026) from Excel
- Merges Feb–Apr 2026 from backup files
- Handles roll promotions and reassignments

**When to use**:
- Full data rebuild from scratch
- After major data corruption

---

### compare_backups.py
**Purpose**: Compare two backup JSON files and show differences

**Usage**:
```bash
python scripts/compare_backups.py
```

---

### analyze_backup_duplicates.py
**Purpose**: Detect duplicate entries across backup files

**Usage**:
```bash
python scripts/analyze_backup_duplicates.py
```

---

### show_active_students.py
**Purpose**: Display currently active students from the data file

**Usage**:
```bash
python scripts/show_active_students.py
```

---

### check_backup_matches.py
**Purpose**: Verify backup file integrity against current data

**Usage**:
```bash
python scripts/check_backup_matches.py
```

---

### check_excel_rolls.py
**Purpose**: Validate roll numbers in the Excel source against the data file

**Usage**:
```bash
python scripts/check_excel_rolls.py
```

---

### publish_public_scoreboard.ps1
**Purpose**: Export current data to static public scoreboard (Cloudflare/GitHub Pages)

**Usage**:
```powershell
.\scripts\publish_public_scoreboard.ps1        # Export only
.\scripts\publish_public_scoreboard.ps1 -Push   # Export + git push
```

**What it does**:
- Commits and pushes `public_site/` files: `index.html`, `scores.json`, `offline_scoreboard.html`, `static/css/offline-scoreboard.css`, `_headers`, `README.md`
- SPA files are synced from `app/static/` by the backend's `_sync_spa_to_public_site()` during Force Publish (injects `<meta name="ea-backend-url">` tag with tunnel origin)
- This script is a manual fallback; primary publish path is via LAN admin Force Publish

---

## Data Path Note

**IMPORTANT**: The Flask app resolves the data file path dynamically via `_storage_root_path()`:
1. `EA_STORAGE_ROOT` env var (explicit override)
2. `RENDER_DISK_PATH/ea_tutorial_hub` (Render)
3. `/var/data/ea_tutorial_hub` (LAN server default)
4. Flask `instance_path` (fallback)

Scripts that hardcode `instance/` or `C:/var/data/` may target the wrong file.
Always verify with `python scripts/check_storage_root.py` (now in `archive/incident-scripts/`) or check `EA_STORAGE_ROOT`.

## Best Practices

1. **Always backup before running**: Scripts modify data files
2. **Run during off-hours**: Minimize impact on active users
3. **Verify data path**: Ensure the script targets the same file the Flask app uses
4. **Test in development first**: Before running in production

## Adding New Scripts

When adding new utility scripts:
1. Place them in this `scripts/` directory
2. Add documentation to this README
3. Use `app.utils.data_paths.get_data_path()` for file path resolution (Phase 2)
4. Include usage examples
5. Add error handling
6. Create backups before modifying data
7. **One-off incident scripts** → place in `archive/incident-scripts/` instead
