"""
Remove Sakshi's old roll EA24C06 from students array in LIVE database.

Historical data (month_students, month_roster_profiles) should remain intact.
Only removing from students array to prevent duplicate appearance in Record Score tab.

LIVE PATH: C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json

Run from project root: python scripts/remove_sakshi_old_roll_from_students.py
"""

import json
import sys
from datetime import datetime
import shutil

LIVE_PATH = r'C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json'

OLD_ROLL = 'EA24C06'
NEW_ROLL = 'EA24D32'

# Backup first
backup_path = LIVE_PATH.replace('.json', f'.bak_remove_old_roll_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
shutil.copy2(LIVE_PATH, backup_path)
print(f'Backup created: {backup_path}')

# Load data
with open(LIVE_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

students = data.get('students', [])

# Find all entries with old roll
old_entries = [s for s in students if s.get('roll') == OLD_ROLL]
new_entries = [s for s in students if s.get('roll') == NEW_ROLL]

print(f'\nFound {len(old_entries)} entries with old roll {OLD_ROLL}:')
for entry in old_entries:
    print(f'  - id={entry.get("id")}, name={entry.get("name")}, active={entry.get("active")}')

print(f'\nFound {len(new_entries)} entries with new roll {NEW_ROLL}:')
for entry in new_entries:
    print(f'  - id={entry.get("id")}, name={entry.get("name")}, active={entry.get("active")}')

if not old_entries:
    print('\nNo old roll entries found. Nothing to do.')
    sys.exit(0)

# Remove old roll entries from students array
original_count = len(students)
data['students'] = [s for s in students if s.get('roll') != OLD_ROLL]
removed_count = original_count - len(data['students'])

print(f'\nRemoved {removed_count} old roll entries from students array')
print(f'Original students count: {original_count}')
print(f'New students count: {len(data["students"])}')

# Verify new roll still exists
new_roll_still_exists = any(s.get('roll') == NEW_ROLL for s in data['students'])
if not new_roll_still_exists:
    print(f'\nWARNING: New roll {NEW_ROLL} not found in students array after removal!')
    sys.exit(1)

print(f'\nNew roll {NEW_ROLL} still present in students array ✓')

# Dry-run summary
print('\n=== Fix summary ===')
print(f'  • Remove {removed_count} entries with roll {OLD_ROLL} from students array')
print(f'  • Keep entries with roll {NEW_ROLL} ({len(new_entries)} entries)')
print(f'  • Historical data (month_students, month_roster_profiles) unchanged')
print()

answer = input('Apply these changes to LIVE database? [y/N] ').strip().lower()
if answer != 'y':
    print('Aborted — no changes written.')
    sys.exit(0)

# Write back
with open(LIVE_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('Done — changes written to', LIVE_PATH)
