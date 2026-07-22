"""
One-shot repair for March 2026 Record Score issues.

Actions:
  1. Reactivate student id:4  (Sahil Yadav, EA24C02)
  2. Reactivate student id:63 (Adarsh Arya, EA25C10)
  3. Copy 5 missing Feb 2026 profiles into Mar 2026 roster
     (EA24A03, EA25C11, EA25C20, EA25C23, EA25D21)
     with month_star_count = Feb carry-in + Feb score delta
  4. Add those 5 rolls to month_students['2026-03']

Run from the project root:  python scripts/repair_mar2026_roster.py
"""

import json
import os
import sys
from copy import deepcopy

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'offline_scoreboard_data.json')

REACTIVATE_IDS = {4, 63}          # Sahil (id:4), Adarsh (id:63)
RESTORE_ROLLS  = ['EA24A03', 'EA25C11', 'EA25C20', 'EA25C23', 'EA25D21']

# ── helpers ────────────────────────────────────────────────────────────────────

def roll_norm(r):
    return str(r or '').strip().upper()

def score_delta(scores, student_id, month):
    """Sum of stars awarded to student in a given month (positive deltas only)."""
    return sum(
        max(0, int(s.get('stars') or 0))
        for s in scores
        if s.get('studentId') == student_id and str(s.get('month') or '') == month
    )

# ── load ───────────────────────────────────────────────────────────────────────

with open(DB_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

students     = data.get('students', [])
scores       = data.get('scores', [])
mrp          = data.get('month_roster_profiles', {})
ms           = data.get('month_students', {})

by_id   = {s['id']: s for s in students if 'id' in s}
by_roll = {}
for s in students:
    rk = roll_norm(s.get('roll'))
    if rk and rk not in by_roll:
        by_roll[rk] = s

feb_profiles = mrp.get('2026-02', [])
mar_profiles = mrp.get('2026-03', [])
mar_rolls_set = {roll_norm(p.get('roll')) for p in mar_profiles}
mar_students  = list(ms.get('2026-03', []))

changes = []

# ── 1 & 2: reactivate by studentId ────────────────────────────────────────────

for sid in sorted(REACTIVATE_IDS):
    student = by_id.get(sid)
    if not student:
        print(f'  [WARN] Student id={sid} not found in students list — skipped.')
        continue
    roll = roll_norm(student.get('roll'))
    name = student.get('base_name') or student.get('name') or roll
    if student.get('active') is False:
        student['active'] = True
        changes.append(f'Reactivated id={sid} ({roll} — {name})')
    else:
        changes.append(f'id={sid} ({roll} — {name}) was already active — no change needed')

# ── 3: copy missing Feb profiles into Mar ─────────────────────────────────────

feb_by_roll = {roll_norm(p.get('roll')): p for p in feb_profiles}

for roll in RESTORE_ROLLS:
    rk = roll_norm(roll)
    if rk in mar_rolls_set:
        changes.append(f'{rk}: already in Mar 2026 profile — skipped')
        continue
    feb_p = feb_by_roll.get(rk)
    if not feb_p:
        changes.append(f'{rk}: NOT FOUND in Feb 2026 profiles — skipped')
        continue

    # Compute Mar carry-in = Feb carry-in + Feb positive star delta
    feb_carry_in = max(0, int(feb_p.get('month_star_count') or 0))
    feb_veto_in  = max(0, int(feb_p.get('month_veto_count') or 0))

    # Find studentId for this roll (prefer Feb profile's studentId if present)
    feb_sid = feb_p.get('studentId')
    if not feb_sid:
        stu = by_roll.get(rk)
        feb_sid = stu.get('id') if stu else None

    star_delta_feb = score_delta(scores, feb_sid, '2026-02') if feb_sid else 0
    veto_delta_feb = 0  # vetos don't accumulate the same way; carry-in stays as-is

    mar_star_carry = feb_carry_in + star_delta_feb

    new_profile = {
        'roll':               feb_p.get('roll', rk),
        'name':               feb_p.get('name', ''),
        'base_name':          feb_p.get('base_name', ''),
        'class':              feb_p.get('class'),
        'month_star_count':   mar_star_carry,
        'month_veto_count':   feb_veto_in + veto_delta_feb,
        'month_designations': list(feb_p.get('month_designations') or []),
    }
    if feb_sid:
        new_profile['studentId'] = feb_sid

    mar_profiles.append(new_profile)
    mar_rolls_set.add(rk)
    changes.append(
        f'{rk}: added to Mar 2026 profiles '
        f'(star carry-in={mar_star_carry}, veto carry-in={new_profile["month_veto_count"]})'
    )

# ── 4: sync month_students['2026-03'] ─────────────────────────────────────────

mar_ms_set = {roll_norm(r) for r in mar_students}
for roll in RESTORE_ROLLS:
    rk = roll_norm(roll)
    if rk not in mar_ms_set:
        mar_students.append(rk)
        mar_ms_set.add(rk)
        changes.append(f'{rk}: added to month_students[2026-03]')

# ── dry-run summary ────────────────────────────────────────────────────────────

print('\n=== Repair summary (DRY RUN) ===')
for c in changes:
    print(f'  • {c}')
print()

if not changes:
    print('Nothing to do — all records are already correct.')
    sys.exit(0)

answer = input('Apply these changes? [y/N] ').strip().lower()
if answer != 'y':
    print('Aborted — no changes written.')
    sys.exit(0)

# ── write back ────────────────────────────────────────────────────────────────

data['month_roster_profiles']['2026-03'] = mar_profiles
data['month_students']['2026-03'] = mar_students

with open(DB_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('Done — changes written to', DB_PATH)
