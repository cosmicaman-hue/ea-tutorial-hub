#!/usr/bin/env python3
"""
Fix: Set active_from_month on students whose rolls were reassigned
but who lack active_from_month, causing them to be hidden by roll_history checks.

Also updates last_month_appeared where stale.

Creates backup before modifying.
"""
import json, shutil
from pathlib import Path
from datetime import datetime

LIVE_PATH = Path("C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json")
data_path = LIVE_PATH if LIVE_PATH.exists() else Path("instance/offline_scoreboard_data.json")
print(f"Using: {data_path}")

# Backup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = data_path.parent / f"{data_path.stem}.bak-active-from-fix-{timestamp}.json"
shutil.copy2(data_path, backup_path)
print(f"Backup: {backup_path}")

with open(data_path, 'r', encoding='utf-8') as f:
    d = json.load(f)

students = d.get('students', [])
roll_history = d.get('roll_history', [])
profiles = d.get('month_roster_profiles', {})

# Build map: old_roll -> effective_month for each roll_history entry
retired_rolls = {}
for entry in roll_history:
    old_roll = entry.get('old_roll', '')
    effective = entry.get('effective_month', '')
    if old_roll and effective:
        retired_rolls[old_roll] = effective

# For each student with a retired roll, determine when they first appeared
# with that roll in roster profiles
def find_first_month_with_roll(roll, student_id, profiles):
    """Find the first month where this student_id appears with this roll in roster profiles."""
    first_month = None
    for month in sorted(profiles.keys()):
        p_list = profiles[month]
        for p in p_list:
            if p.get('roll') == roll and p.get('studentId') == student_id:
                if first_month is None or month < first_month:
                    first_month = month
    return first_month

# Students that need active_from_month set
fixes = []
for s in students:
    roll = s.get('roll', '')
    sid = s.get('id')
    afm = s.get('active_from_month')
    
    if roll in retired_rolls:
        effective = retired_rolls[roll]
        # Check if this student is the one who vacated the roll
        hist_sid = None
        for entry in roll_history:
            if entry.get('old_roll') == roll:
                hist_sid = entry.get('student_id')
                break
        
        # If this student is NOT the one who vacated, they need active_from_month
        if str(sid) != str(hist_sid):
            if not afm or afm < effective:
                # Find when they first appeared with this roll
                first_month = find_first_month_with_roll(roll, sid, profiles)
                if not first_month:
                    # Fallback: use effective month (same month as roll change)
                    first_month = effective
                
                fixes.append({
                    'roll': roll,
                    'id': sid,
                    'name': s.get('name'),
                    'current_afm': afm,
                    'effective': effective,
                    'new_afm': first_month,
                    'hist_sid': hist_sid
                })

print(f"\nStudents needing active_from_month fix: {len(fixes)}")
for fix in fixes:
    print(f"  {fix['roll']} (id={fix['id']}, {fix['name']}): "
          f"active_from_month {fix['current_afm']} -> {fix['new_afm']} "
          f"(effective={fix['effective']}, vacated_by_id={fix['hist_sid']})")

# Apply fixes
for fix in fixes:
    for s in students:
        if s.get('id') == fix['id'] and s.get('roll') == fix['roll']:
            s['active_from_month'] = fix['new_afm']
            print(f"  ✓ Set active_from_month={fix['new_afm']} on {fix['roll']} ({fix['name']})")

# Also update last_month_appeared for active students where it's stale
current_month = "2026-04"
stale_lma = []
for s in students:
    if s.get('active', True) and s.get('last_month_appeared', '') < current_month:
        # Check if they have scores in more recent months
        sid = s.get('id')
        has_recent = any(
            sc.get('studentId') == sid and sc.get('date', '')[:7] >= current_month
            for sc in d.get('scores', [])
        )
        if has_recent or s.get('roll') in [f['roll'] for f in fixes]:
            old_lma = s.get('last_month_appeared', '')
            s['last_month_appeared'] = current_month
            stale_lma.append(f"{s.get('roll')} ({s.get('name')}): {old_lma} -> {current_month}")

if stale_lma:
    print(f"\nUpdated last_month_appeared for {len(stale_lma)} students:")
    for item in stale_lma:
        print(f"  {item}")

# Save
with open(data_path, 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print(f"\n✓ Data saved to {data_path}")
print("  Please refresh the browser to pick up changes.")
