"""Diagnose why EA24A03 / EA24A05 are invisible from Oct 2024 onwards."""
import json, sys

DB = r'C:\var\data\ea_tutorial_hub\offline_scoreboard_data.json'
ROLLS = {'EA24A03', 'EA24A05'}

with open(DB, 'r', encoding='utf-8') as f:
    db = json.load(f)

students   = db.get('students', [])
roll_hist  = db.get('roll_history', [])
profiles   = db.get('month_roster_profiles', {})
m_students = db.get('month_students', {})

# ── 1. Students with these rolls ──────────────────────────────────────────────
print("=== Students with EA24A03 / EA24A05 ===")
target_ids = set()
for s in students:
    if s.get('roll') in ROLLS:
        target_ids.add(s['id'])
        print(f"  id={s['id']}  roll={s['roll']}  name={s.get('base_name') or s.get('name')}  "
              f"active={s.get('active')}  deact={s.get('deactivation_month')}  "
              f"last_seen={s.get('last_month_appeared')}  "
              f"rolls_by_month={s.get('rolls_by_month')}")

# ── 2. Roll-history entries ────────────────────────────────────────────────────
print("\n=== Roll history for these rolls ===")
for rh in roll_hist:
    if rh.get('old_roll') in ROLLS or rh.get('new_roll') in ROLLS:
        print(f"  {rh}")

# ── 3. month_roster_profiles ──────────────────────────────────────────────────
print("\n=== month_roster_profiles appearance ===")
for month in sorted(profiles.keys()):
    for p in profiles[month]:
        if p.get('roll') in ROLLS:
            print(f"  {month}: roll={p['roll']}  name={p.get('base_name') or p.get('name')}  "
                  f"studentId={p.get('studentId')}")

# ── 4. month_students (legacy roster) ─────────────────────────────────────────
print("\n=== month_students appearance ===")
for month in sorted(m_students.keys()):
    for r in m_students[month]:
        if r in ROLLS:
            print(f"  {month}: {r}")

# ── 5. Score count per month for these students ────────────────────────────────
print("\n=== Scores per month ===")
scores = db.get('scores', [])
from collections import defaultdict
by_id_month = defaultdict(int)
for sc in scores:
    if sc.get('studentId') in target_ids:
        by_id_month[(sc['studentId'], sc.get('month', ''))] += 1
for (sid, mo), cnt in sorted(by_id_month.items()):
    sname = next((s.get('base_name') or s.get('name') for s in students if s['id'] == sid), '?')
    print(f"  id={sid} ({sname})  {mo}: {cnt} scores")
