#!/usr/bin/env python3
"""
Restore Feb 2026 data from backup snapshot and harden it against future changes.
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

# Paths
CURRENT_DATA = Path("instance/offline_scoreboard_data.json")
BACKUP_SOURCE = Path("instance/startup_restore_points/offline_scoreboard_startup_20260318_125950.json")
RESTORE_BACKUP = Path(f"instance/offline_scoreboard_data.pre_feb2026_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

print("=" * 60)
print("Feb 2026 Data Restoration Script")
print("=" * 60)

# Step 1: Create backup of current state
print("\n[1/5] Creating backup of current state...")
shutil.copy2(CURRENT_DATA, RESTORE_BACKUP)
print(f"✓ Backup saved: {RESTORE_BACKUP}")

# Step 2: Load current and backup data
print("\n[2/5] Loading data files...")
with open(CURRENT_DATA, 'r', encoding='utf-8') as f:
    current_data = json.load(f)
    
with open(BACKUP_SOURCE, 'r', encoding='utf-8') as f:
    backup_data = json.load(f)

print(f"✓ Current data loaded: {len(current_data.get('scores', []))} total scores")
print(f"✓ Backup data loaded: {len(backup_data.get('scores', []))} total scores")

# Step 3: Extract Feb 2026 data from backup
print("\n[3/5] Extracting Feb 2026 data from backup...")

# Extract Feb 2026 scores
backup_feb_scores = [
    s for s in backup_data.get('scores', [])
    if s.get('month') == '2026-02' or (s.get('date', '')[:7] == '2026-02')
]

# Extract Feb 2026 month_roster_profiles
backup_feb_profiles = backup_data.get('month_roster_profiles', {}).get('2026-02', [])

# Extract Feb 2026 month_students
backup_feb_students = backup_data.get('month_students', {}).get('2026-02', [])

# Extract Feb 2026 month_student_extras
backup_feb_extras = backup_data.get('month_student_extras', {}).get('2026-02', {})

print(f"✓ Found {len(backup_feb_scores)} Feb 2026 scores in backup")
print(f"✓ Found {len(backup_feb_profiles)} Feb 2026 profiles in backup")
print(f"✓ Found {len(backup_feb_students)} Feb 2026 students in backup")

# Show sample scores
if backup_feb_scores:
    sample = backup_feb_scores[0]
    print(f"\nSample Feb 2026 score from backup:")
    print(f"  Student ID: {sample.get('studentId')}")
    print(f"  Date: {sample.get('date')}")
    print(f"  Points: {sample.get('points')}")
    print(f"  Notes: {sample.get('notes', '')[:50]}...")

# Step 4: Remove current Feb 2026 data and replace with backup
print("\n[4/5] Replacing Feb 2026 data with backup...")

# Remove all current Feb 2026 scores
current_data['scores'] = [
    s for s in current_data.get('scores', [])
    if not (s.get('month') == '2026-02' or (s.get('date', '')[:7] == '2026-02'))
]

# Add backup Feb 2026 scores
current_data['scores'].extend(backup_feb_scores)

# Replace Feb 2026 month data
if 'month_roster_profiles' not in current_data:
    current_data['month_roster_profiles'] = {}
current_data['month_roster_profiles']['2026-02'] = backup_feb_profiles

if 'month_students' not in current_data:
    current_data['month_students'] = {}
current_data['month_students']['2026-02'] = backup_feb_students

if 'month_student_extras' not in current_data:
    current_data['month_student_extras'] = {}
current_data['month_student_extras']['2026-02'] = backup_feb_extras

print(f"✓ Removed old Feb 2026 data")
print(f"✓ Restored {len(backup_feb_scores)} Feb 2026 scores from backup")
print(f"✓ Restored {len(backup_feb_profiles)} Feb 2026 profiles from backup")

# Step 5: Add hardening metadata
print("\n[5/5] Hardening Feb 2026 month...")

if 'frozen_months' not in current_data:
    current_data['frozen_months'] = {}

current_data['frozen_months']['2026-02'] = {
    'frozen_at': datetime.now().isoformat(),
    'frozen_by': 'admin',
    'reason': 'Historical month restoration and hardening',
    'source_backup': str(BACKUP_SOURCE),
    'score_count': len(backup_feb_scores),
    'profile_count': len(backup_feb_profiles),
    'allow_modifications': False,
    'hardened': True
}

print("✓ Feb 2026 marked as frozen and hardened")

# Save the restored data
print("\n[6/6] Saving restored data...")
with open(CURRENT_DATA, 'w', encoding='utf-8') as f:
    json.dump(current_data, f, indent=2, ensure_ascii=False)

print(f"✓ Data saved to {CURRENT_DATA}")

# Summary
print("\n" + "=" * 60)
print("RESTORATION COMPLETE!")
print("=" * 60)
print(f"\n✓ Feb 2026 data restored from: {BACKUP_SOURCE}")
print(f"✓ {len(backup_feb_scores)} scores restored")
print(f"✓ {len(backup_feb_profiles)} profiles restored")
print(f"✓ Month hardened against future modifications")
print(f"\nBackup of previous state: {RESTORE_BACKUP}")
print("\nNext steps:")
print("1. Hard refresh browser (Ctrl+Shift+R)")
print("2. Navigate to Feb 2026 scoreboard")
print("3. Verify all students show correct scores (not 0)")
print("\nIf issues occur, restore from backup:")
print(f'  Copy-Item "{RESTORE_BACKUP}" "{CURRENT_DATA}" -Force')
