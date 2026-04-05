# Migration Scripts

This directory contains one-time migration scripts for system updates and data transformations.

## Migration Scripts

### migrate_to_secure_credentials.py
**Purpose**: Migrate passwords from environment variables to encrypted storage

**Status**: ✅ Completed (One-time migration)

**What it does**:
1. Backs up environment variables to `instance/env_backup.json`
2. Migrates ADMIN_PASSWORD to secure storage
3. Migrates TEACHER_PASSWORD to secure storage
4. Migrates EA_JOIN_CODE to secure storage
5. Verifies migration success

**When to use**:
- Initial setup after deploying secrets manager
- Moving from environment-based to encrypted credential storage

**Usage**:
```bash
python migrations/migrate_to_secure_credentials.py
```

**Output**:
- Encrypted credentials in `instance/secrets/credentials.json`
- Backup of environment variables in `instance/env_backup.json`
- Verification report

---

### migrate_veto_system.py
**Purpose**: Migrate from complex veto tracking to simplified system

**Status**: ✅ Completed (One-time migration)

**What it does**:
1. Creates backup of existing data
2. Loads student VETO data
3. Initializes new simplified VETO system
4. Preserves all existing allocations
5. Hardens the system

**When to use**:
- Initial migration from old VETO system
- Consolidating VETO tracking into single system

**Usage**:
```bash
python migrations/migrate_veto_system.py
```

**Output**:
- Updated `instance/offline_scoreboard_data.json` with new VETO structure
- Backup file created
- Migration summary

---

## Running Migrations

### Important Notes
⚠️ **Migrations are one-time operations**
- They modify production data
- Always backup before running
- Run during maintenance windows
- Test in development first

### From Project Root
```bash
# Migrate credentials
python migrations/migrate_to_secure_credentials.py

# Migrate VETO system
python migrations/migrate_veto_system.py
```

## Migration Status

| Migration | Status | Date | Notes |
|-----------|--------|------|-------|
| migrate_to_secure_credentials.py | ✅ Done | 2026-03-20 | Credentials now encrypted |
| migrate_veto_system.py | ✅ Done | 2026-03-20 | VETO system simplified |

## Rollback Procedures

### If Credentials Migration Fails
1. Restore from `instance/env_backup.json`
2. Revert to environment variables
3. Check `instance/secrets/` for partial data
4. Re-run migration after fixing issues

### If VETO Migration Fails
1. Restore from `instance/offline_scoreboard_data_backup_*.json`
2. Check migration logs for error details
3. Fix underlying issues
4. Re-run migration

## Adding New Migrations

When creating new migration scripts:

1. **Naming Convention**: `migrate_<feature>_<date>.py`
2. **Always backup**: Create backups before modifying data
3. **Idempotent**: Should be safe to run multiple times
4. **Logging**: Log all changes and results
5. **Verification**: Include verification steps
6. **Documentation**: Update this README
7. **Testing**: Test thoroughly in development

### Migration Template
```python
#!/usr/bin/env python3
"""
Migration: <Description>
Date: <Date>
Purpose: <What this migration does>
"""
import json
import shutil
from pathlib import Path
from datetime import datetime

def backup_data(data_path):
    """Create backup before migration"""
    backup_path = data_path.parent / f"{data_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy2(data_path, backup_path)
    print(f"✓ Backup created: {backup_path}")
    return backup_path

def migrate():
    """Execute migration"""
    data_path = Path('instance/offline_scoreboard_data.json')
    
    # Backup first
    backup_data(data_path)
    
    # Load data
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Perform migration
    # ... migration logic here ...
    
    # Save changes
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("✓ Migration completed successfully")

if __name__ == '__main__':
    migrate()
```

## Migration History

### 2026-03-20
- ✅ Migrated credentials to encrypted storage
- ✅ Simplified VETO system architecture
- ✅ Reorganized project structure

## Support

For migration issues:
1. Check the migration logs
2. Review the backup files
3. Consult the README for your specific migration
4. Contact the development team if needed
