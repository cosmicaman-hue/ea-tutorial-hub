#!/usr/bin/env python3
"""Verify the active_from_month fix was applied correctly."""
import json
from pathlib import Path

LIVE_PATH = Path("C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json")
with open(LIVE_PATH, 'r', encoding='utf-8') as f:
    d = json.load(f)

targets = ['EA24A05', 'EA24A03', 'EA24C06']
print("=== VERIFICATION ===")
for s in d.get('students', []):
    roll = s.get('roll', '')
    if roll in targets:
        print(f"  {roll}: id={s.get('id')} name={s.get('name')} "
              f"active_from_month={s.get('active_from_month')} "
              f"last_month_appeared={s.get('last_month_appeared')} "
              f"active={s.get('active')}")

# Simulate the JS visibility check
roll_history = d.get('roll_history', [])
retired_rolls = {}
for entry in roll_history:
    old_roll = entry.get('old_roll', '')
    effective = entry.get('effective_month', '')
    student_id = entry.get('student_id')
    if old_roll and effective:
        retired_rolls[old_roll] = (effective, student_id)

print("\n=== VISIBILITY SIMULATION (with JS fix: < instead of <=) ===")
for s in d.get('students', []):
    roll = s.get('roll', '')
    if roll in targets and roll in retired_rolls:
        effective, hist_sid = retired_rolls[roll]
        afm = s.get('active_from_month', '')
        sid = s.get('id')
        
        # Check 1: Is this the student who vacated the roll?
        is_vacator = str(sid) == str(hist_sid)
        # Check 2: active_from_month check (with < instead of <=)
        if not afm:
            visible = False
            reason = f"no active_from_month"
        elif afm < effective:
            visible = False
            reason = f"active_from_month ({afm}) < effective ({effective})"
        else:
            visible = True
            reason = f"active_from_month ({afm}) >= effective ({effective})"
        
        status = "✅ VISIBLE" if (not is_vacator and visible) else "❌ HIDDEN"
        print(f"  {roll} ({s.get('name')}): {status} — vacator={is_vacator}, {reason}")
