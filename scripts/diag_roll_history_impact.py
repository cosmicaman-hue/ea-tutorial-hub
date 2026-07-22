#!/usr/bin/env python3
"""Check which students are hidden by roll_history entries that lack student_id."""
import json
from pathlib import Path

LIVE_PATH = Path("C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json")
data_path = LIVE_PATH if LIVE_PATH.exists() else Path("instance/offline_scoreboard_data.json")

with open(data_path, 'r', encoding='utf-8') as f:
    d = json.load(f)

roll_history = d.get('roll_history', [])
students = d.get('students', [])

print("=== ROLL HISTORY ENTRIES ===")
for entry in roll_history:
    print(f"  old_roll={entry.get('old_roll')} -> new_roll={entry.get('new_roll')} "
          f"effective_month={entry.get('effective_month')} student_id={entry.get('student_id')}")

print("\n=== STUDENTS AFFECTED BY ROLL HISTORY (missing active_from_month) ===")
# For each roll_history entry, find current students with the old_roll
for entry in roll_history:
    old_roll = entry.get('old_roll', '')
    effective = entry.get('effective_month', '')
    hist_sid = entry.get('student_id')
    
    if not old_roll:
        continue
    
    # Find current students with this roll
    for s in students:
        if s.get('roll', '') == old_roll:
            afm = s.get('active_from_month')
            is_affected = not afm or afm <= effective
            if is_affected:
                print(f"  ❌ {s.get('roll')} (id={s.get('id')}, name={s.get('name')}) "
                      f"active_from_month={afm} <= effective={effective} → HIDDEN by roll_history")
            else:
                print(f"  ✅ {s.get('roll')} (id={s.get('id')}, name={s.get('name')}) "
                      f"active_from_month={afm} > effective={effective} → VISIBLE")

print("\n=== WHO SHOULD BE THE student_id IN ROLL HISTORY? ===")
for entry in roll_history:
    old_roll = entry.get('old_roll', '')
    new_roll = entry.get('new_roll', '')
    if not old_roll or not new_roll:
        continue
    # Find student who currently has the new_roll (they're the one who changed)
    changer = next((s for s in students if s.get('roll', '') == new_roll), None)
    if changer:
        print(f"  {old_roll} -> {new_roll}: student_id should be {changer.get('id')} ({changer.get('name')})")
    else:
        # Check roster profiles for who had the old_roll before the change
        profiles = d.get('month_roster_profiles', {})
        before_month = str(int(effective[:4]) - 1) + effective[4:] if effective else ''
        # Just check the month before effective
        print(f"  {old_roll} -> {new_roll}: No current student with new_roll={new_roll}")
