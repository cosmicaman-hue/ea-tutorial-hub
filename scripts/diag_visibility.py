#!/usr/bin/env python3
"""Diagnose visibility of EA24A05 and EA24A03 - check last_month_appeared and historical roster integrity."""
import json
from pathlib import Path

LIVE_PATH = Path("C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json")
data_path = LIVE_PATH if LIVE_PATH.exists() else Path("instance/offline_scoreboard_data.json")
print(f"Using: {data_path}")

with open(data_path, 'r', encoding='utf-8') as f:
    d = json.load(f)

TARGET_ROLLS = ('EA24A05', 'EA24A03')

# 1. Student fields that affect visibility
print("\n" + "="*60)
print("1. STUDENT VISIBILITY FIELDS")
print("="*60)
for s in d.get('students', []):
    roll = s.get('roll', '')
    if roll in TARGET_ROLLS:
        print(f"  {roll}:")
        print(f"    id={s.get('id')}")
        print(f"    name={s.get('name')}")
        print(f"    active={s.get('active')}")
        print(f"    last_month_appeared={s.get('last_month_appeared', 'N/A')}")
        print(f"    deactivation_month={s.get('deactivation_month', 'N/A')}")
        print(f"    active_from_month={s.get('active_from_month', 'N/A')}")
        print(f"    stars={s.get('stars', 0)}")
        print(f"    computed_total_score={s.get('computed_total_score', 0)}")

# 2. Check which months they have scores in
print("\n" + "="*60)
print("2. SCORES BY MONTH")
print("="*60)
for roll in TARGET_ROLLS:
    student = next((s for s in d.get('students', []) if s.get('roll') == roll), None)
    sid = student.get('id') if student else None
    scores = [s for s in d.get('scores', []) if s.get('studentId') == sid] if sid else []
    month_totals = {}
    for s in scores:
        month = s.get('date', '')[:7]
        if month not in month_totals:
            month_totals[month] = {'stars': 0, 'vetos': 0, 'count': 0}
        month_totals[month]['stars'] += s.get('stars', 0)
        month_totals[month]['vetos'] += s.get('vetos', 0)
        month_totals[month]['count'] += 1
    print(f"\n  {roll} (id={sid}):")
    for month in sorted(month_totals.keys()):
        t = month_totals[month]
        print(f"    {month}: {t['count']} entries, stars={t['stars']}, vetos={t['vetos']}")

# 3. Roster profile check - which months have them, which don't
print("\n" + "="*60)
print("3. ROSTER PROFILE PRESENCE")
print("="*60)
profiles = d.get('month_roster_profiles', {})
all_months = sorted(profiles.keys())
for roll in TARGET_ROLLS:
    present = []
    missing = []
    for month in all_months:
        p_list = profiles[month]
        in_roster = any(p.get('roll') == roll for p in p_list)
        if in_roster:
            present.append(month)
        else:
            missing.append(month)
    print(f"\n  {roll}:")
    print(f"    Present in {len(present)} months: {', '.join(present)}")
    print(f"    Missing from {len(missing)} months: {', '.join(missing)}")

# 4. Check if recent fixes modified historical month data
print("\n" + "="*60)
print("4. ROSTER PROFILE DETAILS (recent months)")
print("="*60)
for month in ['2026-02', '2026-03', '2026-04']:
    p_list = profiles.get(month, [])
    for roll in TARGET_ROLLS:
        matches = [p for p in p_list if p.get('roll') == roll]
        if matches:
            for m in matches:
                print(f"  {month} | {roll}: name={m.get('name')} stars={m.get('month_star_count',0)} vetos={m.get('month_veto_count',0)} studentId={m.get('studentId','?')} _admin_enrolled={m.get('_admin_enrolled','?')}")
        else:
            print(f"  {month} | {roll}: NOT IN ROSTER")

# 5. Check roll_history for these students
print("\n" + "="*60)
print("5. ROLL HISTORY")
print("="*60)
roll_history = d.get('roll_history', [])
for entry in roll_history:
    old_roll = entry.get('old_roll', '')
    new_roll = entry.get('new_roll', '')
    if old_roll in TARGET_ROLLS or new_roll in TARGET_ROLLS:
        print(f"  old_roll={old_roll} -> new_roll={new_roll} effective_month={entry.get('effective_month')} studentId={entry.get('studentId')}")

# 6. Check if last_month_appeared is cutting off visibility
print("\n" + "="*60)
print("6. LAST_MONTH_APPEARED IMPACT ANALYSIS")
print("="*60)
# Simulate the JS logic: if month > last_month_appeared, student is hidden
for s in d.get('students', []):
    roll = s.get('roll', '')
    if roll in TARGET_ROLLS:
        lma = s.get('last_month_appeared', '')
        print(f"  {roll}: last_month_appeared='{lma}'")
        if lma:
            # Check which months would be blocked
            blocked = [m for m in all_months if m > lma]
            print(f"    Would be INVISIBLE for months after {lma}: {', '.join(blocked)}")
            # But they have scores in those months!
            sid = s.get('id')
            scores_after = [sc for sc in d.get('scores', []) if sc.get('studentId') == sid and sc.get('date', '')[:7] > lma]
            if scores_after:
                months_with_scores = sorted(set(sc.get('date', '')[:7] for sc in scores_after))
                print(f"    BUT has scores in months after {lma}: {', '.join(months_with_scores)}")
