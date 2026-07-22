"""
Fix Sakshi's roll upgrade: Replace EA24C06 with EA24D32 in monthly rosters.

Sakshi's old roll EA24C06 is still appearing in month_students and month_roster_profiles,
causing her to show up in Record Score tabs. Her new roll EA24D32 is not in these rosters.

This script will:
1. Replace EA24C06 with EA24D32 in month_students for all months
2. Replace EA24C06 profile with EA24D32 profile in month_roster_profiles for all months
3. Update the profile data to use the correct student ID (98)

Run from project root: python scripts/fix_sakshi_roll_upgrade.py
"""

import json
import os
import sys

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'offline_scoreboard_data.json')

OLD_ROLL = 'EA24C06'
NEW_ROLL = 'EA24D32'
NEW_STUDENT_ID = 98

# Load data
with open(DB_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

month_students = data.get('month_students', {})
month_roster_profiles = data.get('month_roster_profiles', {})
students = data.get('students', [])

# Get the new student record
new_student = next((s for s in students if s.get('roll') == NEW_ROLL), None)
if not new_student:
    print(f'ERROR: New roll {NEW_ROLL} not found in students list')
    sys.exit(1)

print(f'Found new student: {new_student.get("name")} (id: {new_student.get("id")}, roll: {NEW_ROLL})')

changes = []

# Fix month_students: replace EA24C06 with EA24D32
for month, rolls in month_students.items():
    if OLD_ROLL in rolls:
        if NEW_ROLL not in rolls:
            # Replace old roll with new roll
            rolls.remove(OLD_ROLL)
            rolls.append(NEW_ROLL)
            rolls.sort()  # Keep sorted
            changes.append(f'month_students[{month}]: replaced {OLD_ROLL} with {NEW_ROLL}')
        else:
            # Remove old roll, new roll already exists
            rolls.remove(OLD_ROLL)
            changes.append(f'month_students[{month}]: removed {OLD_ROLL} ({NEW_ROLL} already present)')

# Fix month_roster_profiles: replace EA24C06 profile with EA24D32 profile
for month, profiles in month_roster_profiles.items():
    old_profile = next((p for p in profiles if p.get('roll') == OLD_ROLL), None)
    if old_profile:
        # Check if new profile already exists
        new_profile_exists = any(p.get('roll') == NEW_ROLL for p in profiles)
        
        if new_profile_exists:
            # Remove old profile, new profile already exists
            profiles[:] = [p for p in profiles if p.get('roll') != OLD_ROLL]
            changes.append(f'month_roster_profiles[{month}]: removed {OLD_ROLL} profile ({NEW_ROLL} already present)')
        else:
            # Replace old profile with new profile
            profiles[:] = [p for p in profiles if p.get('roll') != OLD_ROLL]
            
            # Create new profile based on the student record
            new_profile = {
                'roll': NEW_ROLL,
                'name': new_student.get('name', ''),
                'base_name': new_student.get('base_name', ''),
                'class': new_student.get('class'),
                'month_star_count': old_profile.get('month_star_count', 0),
                'month_veto_count': old_profile.get('month_veto_count', 0),
                'month_designations': old_profile.get('month_designations', []),
                'studentId': NEW_STUDENT_ID
            }
            profiles.append(new_profile)
            changes.append(f'month_roster_profiles[{month}]: replaced {OLD_ROLL} profile with {NEW_ROLL} profile (preserved star/veto counts)')

# Dry-run summary
print('\n=== Fix summary (DRY RUN) ===')
for c in changes:
    print(f'  • {c}')
print()

if not changes:
    print('Nothing to do — records are already correct.')
    sys.exit(0)

answer = input('Apply these changes? [y/N] ').strip().lower()
if answer != 'y':
    print('Aborted — no changes written.')
    sys.exit(0)

# Write back
data['month_students'] = month_students
data['month_roster_profiles'] = month_roster_profiles

with open(DB_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('Done — changes written to', DB_PATH)
