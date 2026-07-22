"""
Remove EA24C06 from LIVE database students array.

LIVE PATH: C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json
"""

import json
import sys
from datetime import datetime
import shutil

LIVE_PATH = r'C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json'
OLD_ROLL = 'EA24C06'

# Backup
backup_path = LIVE_PATH.replace('.json', f'.bak_remove_ea24c06_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
shutil.copy2(LIVE_PATH, backup_path)
print(f'Backup created: {backup_path}')

# Load
with open(LIVE_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

students = data.get('students', [])
old_entries = [s for s in students if s.get('roll') == OLD_ROLL]

print(f'Found {len(old_entries)} entries with roll {OLD_ROLL}:')
for e in old_entries:
    print(f'  id={e.get("id")}, name={e.get("name")}, group={e.get("group")}, active={e.get("active")}')

if not old_entries:
    print('No entries found. Exiting.')
    sys.exit(0)

# Remove
original_count = len(students)
data['students'] = [s for s in students if s.get('roll') != OLD_ROLL]
removed = original_count - len(data['students'])

print(f'\nRemoved {removed} entries from students array')
print(f'Original: {original_count}, New: {len(data["students"])}')

answer = input('\nApply to LIVE database? [y/N] ').strip().lower()
if answer != 'y':
    print('Aborted.')
    sys.exit(0)

with open(LIVE_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('Done. Written to', LIVE_PATH)
