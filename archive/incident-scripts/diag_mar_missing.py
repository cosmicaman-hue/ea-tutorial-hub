"""Find active students in Feb 2026 roster but missing from Mar 2026."""
import json, os

path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'offline_scoreboard_data.json')
with open(path, 'r', encoding='utf-8') as f:
    d = json.load(f)

ms = d.get('month_students', {})
mrp = d.get('month_roster_profiles', {})
students = d.get('students', [])
by_roll = {str(s.get('roll', '')).strip().upper(): s for s in students}

feb_rolls = set(str(r).upper() for r in ms.get('2026-02', []))
mar_rolls = set(str(r).upper() for r in ms.get('2026-03', []))

missing = feb_rolls - mar_rolls
added = mar_rolls - feb_rolls

print(f"Feb 2026 roster: {len(feb_rolls)} students")
print(f"Mar 2026 roster: {len(mar_rolls)} students")
print(f"Missing from Mar (in Feb but not Mar): {len(missing)}")
print(f"New in Mar (in Mar but not Feb): {len(added)}")

print(f"\n=== Missing from Mar 2026 ({len(missing)}) ===")
for roll in sorted(missing):
    stu = by_roll.get(roll)
    if stu:
        name = stu.get('base_name') or stu.get('name', '?')
        active = stu.get('active', True)
        cls = stu.get('class', '?')
        # Count their Mar scores
        sid = stu.get('id')
        mar_scores = [s for s in d.get('scores', []) if s.get('studentId') == sid and ('2026-03' in str(s.get('month', '')) + str(s.get('date', '')))]
        print(f"  {roll}: {name} (class={cls}, active={active}, mar_scores={len(mar_scores)})")
    else:
        print(f"  {roll}: NOT IN STUDENTS LIST")

print(f"\n=== New in Mar 2026 ({len(added)}) ===")
for roll in sorted(added):
    stu = by_roll.get(roll)
    if stu:
        name = stu.get('base_name') or stu.get('name', '?')
        print(f"  {roll}: {name}")
    else:
        print(f"  {roll}: NOT IN STUDENTS LIST")

# Also check: are there active students not in either roster?
all_active = {str(s.get('roll', '')).strip().upper() for s in students if s.get('active', True) != False}
not_in_mar = all_active - mar_rolls
print(f"\n=== Active students NOT in Mar 2026 roster ({len(not_in_mar)}) ===")
for roll in sorted(not_in_mar):
    stu = by_roll.get(roll)
    if stu:
        name = stu.get('base_name') or stu.get('name', '?')
        cls = stu.get('class', '?')
        sid = stu.get('id')
        # Check last month they appeared in
        last_month = ''
        for mk in sorted(ms.keys(), reverse=True):
            if roll in set(str(r).upper() for r in ms.get(mk, [])):
                last_month = mk
                break
        print(f"  {roll}: {name} (class={cls}, last_roster={last_month})")
