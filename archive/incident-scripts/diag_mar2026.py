"""Diagnose Mar 2026 roster state and find EA24A03 across months."""
import json, os

path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'offline_scoreboard_data.json')
with open(path, 'r', encoding='utf-8') as f:
    d = json.load(f)

# Show all available months
ms = d.get('month_students', {})
mrp = d.get('month_roster_profiles', {})
print("=== Available months ===")
for mk in sorted(set(list(ms.keys()) + list(mrp.keys()))):
    ms_count = len(ms.get(mk, []))
    mrp_count = len(mrp.get(mk, []))
    print(f"  {mk}: month_students={ms_count}, month_roster_profiles={mrp_count}")

# Check which months have EA24A03
print("\n=== EA24A03 in month_students ===")
for mk in sorted(ms.keys()):
    rolls = [str(r).upper() for r in ms.get(mk, [])]
    if any('EA24A03' in r for r in rolls):
        print(f"  {mk}: YES")

print("\n=== EA24A03 in month_roster_profiles ===")
for mk in sorted(mrp.keys()):
    profiles = mrp.get(mk, [])
    match = [p for p in profiles if 'EA24A03' in str(p.get('roll', '')).upper()]
    if match:
        p = match[0]
        print(f"  {mk}: stars={p.get('month_star_count')}, vetos={p.get('month_veto_count')}, name={p.get('base_name') or p.get('name')}")

# Show Mar 2026 month_students list
print(f"\n=== 2026-03 month_students ({len(ms.get('2026-03', []))}) ===")
for r in sorted(ms.get('2026-03', [])):
    print(f"  {r}")

# Check Feb 2026 roster for EA24A03
print(f"\n=== 2026-02 month_students ({len(ms.get('2026-02', []))}) ===")
feb_rolls = [str(r).upper() for r in ms.get('2026-02', [])]
has_ea24a03_feb = any('EA24A03' in r for r in feb_rolls)
print(f"  EA24A03 in Feb 2026: {has_ea24a03_feb}")

# Check Apr 2026 roster for EA24A03
print(f"\n=== 2026-04 month_students ({len(ms.get('2026-04', []))}) ===")
apr_rolls = [str(r).upper() for r in ms.get('2026-04', [])]
has_ea24a03_apr = any('EA24A03' in r for r in apr_rolls)
print(f"  EA24A03 in Apr 2026: {has_ea24a03_apr}")

# Show student 11 details
stu = [s for s in d.get('students', []) if s.get('id') == 11][0]
print(f"\n=== Student id=11 detail ===")
print(f"  roll={stu.get('roll')}, name={stu.get('base_name') or stu.get('name')}")
print(f"  class={stu.get('class')}, active={stu.get('active')}")
print(f"  joined={stu.get('joined_date') or stu.get('created_at', '')[:10]}")
rh = stu.get('roll_history', [])
if rh:
    print(f"  roll_history: {json.dumps(rh)}")
