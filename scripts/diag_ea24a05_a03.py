#!/usr/bin/env python3
"""Diagnose why EA24A05 and EA24A03 are missing from scoreboard and record score."""
import json
from pathlib import Path

LIVE_PATH = Path("C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json")
INSTANCE_PATH = Path("instance/offline_scoreboard_data.json")

data_path = LIVE_PATH if LIVE_PATH.exists() else INSTANCE_PATH
print(f"Using: {data_path}")

with open(data_path, 'r', encoding='utf-8') as f:
    d = json.load(f)

TARGET_ROLLS = ('EA24A05', 'EA24A03')

# 1. Check students array
print("\n" + "="*60)
print("1. STUDENTS ARRAY")
print("="*60)
for s in d.get('students', []):
    if s.get('roll', '') in TARGET_ROLLS:
        print(f"  roll={s.get('roll')} name={s.get('name')} active={s.get('active')} id={s.get('id')}")

# 2. Check roster profiles
print("\n" + "="*60)
print("2. MONTH ROSTER PROFILES")
print("="*60)
profiles = d.get('month_roster_profiles', {})
for month in sorted(profiles.keys()):
    p_list = profiles[month]
    matches = [p for p in p_list if p.get('roll', '') in TARGET_ROLLS]
    if matches:
        print(f"  {month}:")
        for m in matches:
            print(f"    roll={m.get('roll')} name={m.get('name')} stars={m.get('month_star_count',0)} vetos={m.get('month_veto_count',0)} active={m.get('active','?')} studentId={m.get('studentId','?')}")
    else:
        # Check if any students exist for this month at all
        all_rolls = [p.get('roll','') for p in p_list]
        has_target = any(r in TARGET_ROLLS for r in all_rolls)
        if not has_target:
            pass  # silent - too many months to list

# List months where they're MISSING
print("\n  Months where EA24A05 is MISSING from roster:")
ea24a05_months = set()
ea24a03_months = set()
for month in sorted(profiles.keys()):
    p_list = profiles[month]
    rolls_in_month = [p.get('roll','') for p in p_list]
    if 'EA24A05' not in rolls_in_month:
        ea24a05_months.add(month)
    if 'EA24A03' not in rolls_in_month:
        ea24a03_months.add(month)

all_months = sorted(profiles.keys())
print(f"    EA24A05 missing in: {', '.join(ea24a05_months) if ea24a05_months else 'none'}")
print(f"    EA24A03 missing in: {', '.join(ea24a03_months) if ea24a03_months else 'none'}")

# 3. Check scores
print("\n" + "="*60)
print("3. SCORES")
print("="*60)
for roll in TARGET_ROLLS:
    student = next((s for s in d.get('students', []) if s.get('roll') == roll), None)
    sid = student.get('id') if student else None
    scores_by_roll = [s for s in d.get('scores', []) if s.get('student_roll') == roll or s.get('roll') == roll]
    scores_by_id = [s for s in d.get('scores', []) if s.get('studentId') == sid] if sid else []
    all_scores = scores_by_roll + [s for s in scores_by_id if s not in scores_by_roll]
    print(f"  {roll} (studentId={sid}):")
    print(f"    Scores by roll: {len(scores_by_roll)}")
    print(f"    Scores by studentId: {len(scores_by_id)}")
    if all_scores:
        months_seen = set()
        for s in all_scores:
            dt = s.get('date', '')
            if dt:
                months_seen.add(dt[:7])
        print(f"    Months with scores: {', '.join(sorted(months_seen))}")
        for s in all_scores[:10]:
            print(f"      date={s.get('date')} stars={s.get('stars',0)} vetos={s.get('vetos',0)} studentId={s.get('studentId')} student_roll={s.get('student_roll','')}")

# 4. Check isStudentVisibleForMonth logic
print("\n" + "="*60)
print("4. VISIBILITY ANALYSIS")
print("="*60)
for roll in TARGET_ROLLS:
    student = next((s for s in d.get('students', []) if s.get('roll') == roll), None)
    if not student:
        print(f"  {roll}: NOT IN students[] - this is the root cause!")
        continue
    
    sid = student.get('id')
    is_active = student.get('active', True)
    print(f"  {roll}: active={is_active}, id={sid}")
    
    for month in sorted(profiles.keys()):
        p_list = profiles[month]
        in_roster = any(p.get('roll') == roll for p in p_list)
        has_scores = any(
            (s.get('student_roll') == roll or (sid and s.get('studentId') == sid))
            and s.get('date', '').startswith(month)
            for s in d.get('scores', [])
        )
        visible = in_roster or has_scores
        if not visible and is_active:
            print(f"    {month}: INVISIBLE (not in roster, no scores)")
        elif visible:
            pass  # only show problems

# 5. Summary of all active students missing from recent month rosters
print("\n" + "="*60)
print("5. ALL ACTIVE STUDENTS MISSING FROM RECENT ROSTERS")
print("="*60)
recent_months = sorted(profiles.keys())[-3:]
for month in recent_months:
    p_list = profiles[month]
    roster_rolls = set(p.get('roll','') for p in p_list)
    active_students = [s for s in d.get('students', []) if s.get('active', True)]
    missing = [s for s in active_students if s.get('roll','') not in roster_rolls]
    if missing:
        print(f"  {month}: {len(missing)} active students missing from roster")
        for s in missing:
            print(f"    {s.get('roll')} - {s.get('name')}")
