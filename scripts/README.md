# Utility Scripts

This directory contains utility and maintenance scripts for the EA Tutorial Hub project.

## Scripts

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

**Output**:
- Updates `instance/offline_scoreboard_data.json` with hardened VETO tracking
- Creates automatic backups before changes
- Displays summary of allocations

---

### anti_corruption_check.py
**Purpose**: Verify data integrity and detect corruption

**Usage**:
```bash
python scripts/anti_corruption_check.py
```

**What it does**:
- Validates JSON file structure
- Checks for data inconsistencies
- Detects corrupted records
- Reports integrity issues

**When to use**:
- After system crashes
- Before major operations
- Regular maintenance checks

---

### inject_cache_buster.py
**Purpose**: Inject cache-busting parameters into static assets

**Usage**:
```bash
python scripts/inject_cache_buster.py
```

**What it does**:
- Adds version parameters to CSS/JS files
- Forces browser cache refresh
- Updates HTML references

**When to use**:
- After deploying frontend changes
- When users report stale assets
- During release cycles

---

## Running Scripts

### From Project Root
```bash
# Run VETO manager
python scripts/veto_manager.py

# Run integrity check
python scripts/anti_corruption_check.py

# Run cache buster
python scripts/inject_cache_buster.py
```

### From Within Flask App
```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'scripts'))

from veto_manager import VetoManager
manager = VetoManager()
manager.complete_veto_setup()
```

## Script Dependencies

All scripts depend on:
- `instance/offline_scoreboard_data.json` - Main data file
- Standard Python libraries (json, pathlib, datetime, etc.)

## Best Practices

1. **Always backup before running**: Scripts modify data files
2. **Run during off-hours**: Minimize impact on active users
3. **Check logs after running**: Verify successful execution
4. **Test in development first**: Before running in production

## Troubleshooting

### Script fails to find data file
- Ensure you're running from project root
- Check that `instance/offline_scoreboard_data.json` exists

### Import errors
- Verify Python path includes project root
- Check that all dependencies are installed

### Data corruption detected
- Restore from backup: `instance/offline_scoreboard_data_backup_*.json`
- Re-run the script

## Adding New Scripts

When adding new utility scripts:
1. Place them in this `scripts/` directory
2. Add documentation to this README
3. Include usage examples
4. Document dependencies
5. Add error handling
6. Create backups before modifying data
