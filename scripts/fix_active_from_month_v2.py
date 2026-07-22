#!/usr/bin/env python3
"""Fix active_from_month on EA24A05 and EA24A03 ONLY.
EA24C06 is correctly retired (moved to EA24D32) - do NOT touch it."""
import json, shutil
from pathlib import Path
from datetime import datetime

LIVE_PATH = Path("C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json")
data_path = LIVE_PATH if LIVE_PATH.exists() else Path("instance/offline_scoreboard_data.json")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = data_path.parent / f"{data_path.stem}.bak-afm-v2-{timestamp}.json"
shutil.copy2(data_path, backup_path)
print(f"Backup: {backup_path}")

with open(data_path, 'r', encoding='utf-8') as f:
    d = json.load(f)

students = d.get('students', [])
roll_history = d.get('roll_history', [])
profiles = d.get('month_roster_profiles', {})

retired_rolls = {}
for entry in roll_history:
    old_roll = entry.get('old_roll', '')
    effective = entry.get('effective_month', '')
    hist_sid = entry.get('student_id')
    if old_roll and effective:
        retired_rolls[old_roll] = (effective, hist_sid)

def find_first_month_with_roll(roll, student_id, profiles):
    first_month = None
    for month in sorted(profiles.keys()):
        p_list = profiles.get(month, [])
        for p in p_list:
            if not isinstance(p, dict):
                continue
            p_roll = str(p.get('roll', '')).strip().upper()
            p_sid = p.get('studentId') or p.get('student_id')
            if p_roll == roll and str(p_sid) == str(student_id):
                if first_month is None or month < first_month:
                    first_month = month
    return first_month

TARGET_ROLLS = {'EA24A05', 'EA24A03'}

for s in students:
    roll = s.get('roll', '')
    sid = s.get('id')
    if roll not in TARGET_ROLLS:
        continue
    if roll not in retired_rolls:
        print(f"  {roll} (id={sid}): NOT in roll_history - no fix needed")
        continue
    effective, hist_sid = retired_rolls[roll]
    if str(sid) == str(hist_sid):
        print(f"  {roll} (id={sid}): IS the vacator - no fix needed")
        continue
    afm = s.get('active_from_month')
    if afm and afm >= effective:
        print(f"  {roll} (id={sid}, {s.get('name')}): active_from_month={afm} already OK")
        continue
    first_month = find_first_month_with_roll(roll, sid, profiles)
    if not first_month:
        first_month = effective
    s['active_from_month'] = first_month
    print(f"  FIXED {roll} (id={sid}, {s.get('name')}): active_from_month={afm} -> {first_month}")

# Confirm EA24C06 is NOT touched
for s in students:
    if s.get('roll') == 'EA24C06' and s.get('id') == 88:
        print(f"  EA24C06 (id=88, Sakshi): active_from_month={s.get('active_from_month')} (should be None/empty)")

with open(data_path, 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
print(f"\nSaved to {data_path}")
