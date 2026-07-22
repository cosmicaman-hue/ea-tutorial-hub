"""
Diagnose why deactivated students show in Record Score tab.
Check LIVE database for current month (2026-04) roster vs active students.
"""
import json

LIVE_PATH = r'C:/var/data/ea_tutorial_hub/offline_scoreboard_data.json'

with open(LIVE_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

students = data.get('students', [])
ms = data.get('month_students', {})
mrp = data.get('month_roster_profiles', {})

# Current month
current_month = '2026-04'

# Get deactivated students
deactivated = [s for s in students if s.get('active') is False]
print(f'Total deactivated students: {len(deactivated)}')

# Check deactivated students with deactivation_month but active NOT false
weird = [s for s in students if s.get('deactivation_month') and s.get('active') is not False]
print(f'\nStudents with deactivation_month but active != false: {len(weird)}')
for s in weird:
    print(f'  id={s.get("id")}, roll={s.get("roll")}, name={s.get("name")}, active={s.get("active")}, deactivation_month={s.get("deactivation_month")}')

# Check month_roster_profiles for current month
current_profiles = mrp.get(current_month, [])
current_rolls_in_profiles = set(p.get('roll') for p in current_profiles if p.get('roll'))
current_rolls_in_month_students = set(ms.get(current_month, []))

print(f'\n2026-04 month_roster_profiles: {len(current_profiles)} entries')
print(f'2026-04 month_students: {len(ms.get(current_month, []))} rolls')

# Find deactivated student rolls in current month roster
deactivated_rolls = set(s.get('roll') for s in deactivated)
in_profile = current_rolls_in_profiles & deactivated_rolls
in_month_students = current_rolls_in_month_students & deactivated_rolls

print(f'\nDeactivated rolls in 2026-04 month_roster_profiles: {len(in_profile)}')
for roll in sorted(in_profile):
    s = next((s for s in deactivated if s.get('roll') == roll), None)
    if s:
        print(f'  {roll}: id={s.get("id")}, name={s.get("name")}, group={s.get("group")}')

print(f'\nDeactivated rolls in 2026-04 month_students: {len(in_month_students)}')
for roll in sorted(in_month_students):
    s = next((s for s in deactivated if s.get('roll') == roll), None)
    if s:
        print(f'  {roll}: id={s.get("id")}, name={s.get("name")}, group={s.get("group")}')

# Also check: students with active=true but deactivation_month in the past
# These would pass the active filter but should be hidden by deactivation_month
active_but_deactivated = [s for s in students if s.get('active') is not False and s.get('deactivation_month') and current_month >= str(s.get('deactivation_month', ''))]
print(f'\nActive=True but deactivation_month <= 2026-04: {len(active_but_deactivated)}')
for s in active_but_deactivated:
    print(f'  id={s.get("id")}, roll={s.get("roll")}, name={s.get("name")}, active={s.get("active")}, deactivation_month={s.get("deactivation_month")}')
