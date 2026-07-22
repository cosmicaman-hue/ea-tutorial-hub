"""Diagnose EA24A03 Mar 2026 score total = 0 issue."""
import json, os

path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'offline_scoreboard_data.json')
with open(path, 'r', encoding='utf-8') as f:
    d = json.load(f)

# Find student
students = [s for s in d.get('students', []) if 'EA24A03' in str(s.get('roll', '')).upper()]
if not students:
    print("ERROR: EA24A03 not found in students list!")
else:
    for s in students:
        sid = s.get('id')
        print(f"Student: id={sid}, roll={s.get('roll')}, name={s.get('base_name') or s.get('name')}, class={s.get('class')}, active={s.get('active')}")

        # All scores for this student
        all_scores = [sc for sc in d.get('scores', []) if sc.get('studentId') == sid]
        print(f"  Total score rows: {len(all_scores)}")

        # Group by month
        by_month = {}
        for sc in all_scores:
            mk = sc.get('month') or (str(sc.get('date', ''))[:7] if sc.get('date') else '?')
            by_month.setdefault(mk, []).append(sc)

        for mk in sorted(by_month.keys()):
            rows = by_month[mk]
            total = sum(int(r.get('points', 0)) for r in rows)
            print(f"  {mk}: {len(rows)} rows, total={total}")

        # Detailed Mar 2026
        mar_scores = by_month.get('2026-03', [])
        print(f"\n  Mar 2026 detail ({len(mar_scores)} rows):")
        for sc in mar_scores[:20]:
            print(f"    date={sc.get('date')} pts={sc.get('points')} cat={sc.get('category','')} desc={str(sc.get('description',''))[:40]}")

    # Check month_roster_profiles for Mar 2026
    profiles = d.get('month_roster_profiles', {}).get('2026-03', [])
    match = [p for p in profiles if 'EA24A03' in str(p.get('roll', '')).upper()]
    print(f"\nMonth roster profile for 2026-03: {len(match)} matches")
    for p in match:
        print(f"  roll={p.get('roll')}, name={p.get('base_name') or p.get('name')}, stars={p.get('month_star_count')}, vetos={p.get('month_veto_count')}, locked={p.get('_admin_locked')}")

    # Check month_students for Mar 2026
    ms = d.get('month_students', {}).get('2026-03', [])
    ms_match = [r for r in ms if 'EA24A03' in str(r).upper()]
    print(f"\nMonth students 2026-03: {len(ms_match)} matches out of {len(ms)} total")
