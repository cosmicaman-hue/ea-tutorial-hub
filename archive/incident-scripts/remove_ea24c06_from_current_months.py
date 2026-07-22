"""
Remove EA24C06 from month_roster_profiles and month_students for current/future months only.
Keep historical months (2024-12 to 2026-03) intact.

LIVE PATH: C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json
"""

import json
import sys
from datetime import datetime
import shutil

LIVE_PATH = r'C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json'
OLD_ROLL = 'EA24C06'
NEW_ROLL = 'EA24D32'

# Current month is 2026-04, remove from 2026-04 onwards
CURRENT_MONTH = '2026-04'

# Backup
backup_path = LIVE_PATH.replace('.json', f'.bak_remove_current_months_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
shutil.copy2(LIVE_PATH, backup_path)
print(f'Backup created: {backup_path}')

# Load
with open(LIVE_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

month_students = data.get('month_students', {})
month_roster_profiles = data.get('month_roster_profiles', {})

changes = []

# Remove from month_students for current/future months
for month in list(month_students.keys()):
    if month >= CURRENT_MONTH:
        if OLD_ROLL in month_students[month]:
            month_students[month].remove(OLD_ROLL)
            changes.append(f'month_students[{month}]: removed {OLD_ROLL}')

# Remove from month_roster_profiles for current/future months
for month in list(month_roster_profiles.keys()):
    if month >= CURRENT_MONTH:
        old_profiles = [p for p in month_roster_profiles[month] if p.get('roll') == OLD_ROLL]
        if old_profiles:
            original_count = len(month_roster_profiles[month])
            month_roster_profiles[month] = [p for p in month_roster_profiles[month] if p.get('roll') != OLD_ROLL]
            removed = original_count - len(month_roster_profiles[month])
            changes.append(f'month_roster_profiles[{month}]: removed {removed} profile(s) with {OLD_ROLL}')

print('\n=== Changes to be applied (current/future months only) ===')
for c in changes:
    print(f'  • {c}')

print(f'\nHistorical months (before {CURRENT_MONTH}) will remain unchanged.')

if not changes:
    print('\nNo changes needed for current/future months.')
    sys.exit(0)

answer = input('\nApply these changes to LIVE database? [y/N] ').strip().lower()
if answer != 'y':
    print('Aborted.')
    sys.exit(0)

data['month_students'] = month_students
data['month_roster_profiles'] = month_roster_profiles

with open(LIVE_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('Done. Written to', LIVE_PATH)
