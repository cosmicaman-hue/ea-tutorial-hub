import json, sys
from collections import Counter

DATA_PATH = r'C:\Users\sujit\OneDrive\Desktop\Project EA\instance\offline_scoreboard_data.json'
data = json.load(open(DATA_PATH, 'r', encoding='utf-8'))

# Simulate the EXACT JavaScript rendering path for Ayush in month 2026-03
month = '2026-03'
student_id = 1

# 1. Find the student
student = next(s for s in data['students'] if s['id'] == student_id)
print(f"Student: id={student['id']}, roll={student['roll']}, name={student['name']}, active={student['active']}")

# 2. getScoresForMonth - filter scores to this month
month_scores = [s for s in data['scores'] if s.get('month') == month or (not s.get('month') and str(s.get('date',''))[:7] == month)]
print(f"\nScore entries for {month}: {len(month_scores)}")

# 3. Build scoreByStudent (keyed by studentId)
score_by_student = {}
for s in month_scores:
    sid = s.get('studentId')
    if sid not in score_by_student:
        score_by_student[sid] = []
    score_by_student[sid].append(s)

print(f"scoreByStudent keys: {list(score_by_student.keys())}")
print(f"scoreByStudent[1] count: {len(score_by_student.get(1, []))}")

# 4. isStudentVisibleForMonth simulation
roll_key = str(student['roll'] or '').upper()
print(f"\nrollKey = {roll_key}")

roster = data.get('month_students', {}).get(month, [])
print(f"Legacy roster has EA24A01: {'EA24A01' in roster}")
print(f"Legacy roster has EA24B15: {'EA24B15' in roster}")

profiles = data.get('month_roster_profiles', {}).get(month, [])
# Check inProfileRoster by studentId
in_profile_by_id = any(p.get('studentId') == student_id for p in profiles)
# Check inProfileRoster by roll
in_profile_by_roll = any(str(p.get('roll','')).upper() == roll_key for p in profiles)
# Check inLegacyRoster
in_legacy = roll_key in roster if roll_key else False

print(f"inProfileRoster (by studentId): {in_profile_by_id}")
print(f"inProfileRoster (by roll {roll_key}): {in_profile_by_roll}")
print(f"inLegacyRoster: {in_legacy}")

# 5. getMonthAwareStudent simulation
profile_map_entry = None
for p in profiles:
    if str(p.get('roll','')).upper() == roll_key:
        profile_map_entry = p
        break
if not profile_map_entry:
    # Fallback: search by studentId
    for p in profiles:
        if p.get('studentId') == student_id:
            profile_map_entry = p
            break

if profile_map_entry:
    display_roll = str(profile_map_entry.get('roll','')).upper() or roll_key
    print(f"\ngetMonthAwareStudent -> roll={display_roll}, name={profile_map_entry.get('name')}")
else:
    print(f"\ngetMonthAwareStudent -> NO PROFILE FOUND (would use original student)")
    display_roll = roll_key

# 6. getHistoricalScoreStudentIds simulation
# For historical month, this returns {student.id} plus any matching by roll/name
resolved_ids = {student_id}
print(f"\ngetHistoricalScoreStudentIds: {resolved_ids}")

# 7. Final score retrieval
student_scores = []
for sid in resolved_ids:
    student_scores.extend(score_by_student.get(sid, []))
print(f"studentScores count: {len(student_scores)}")

# 8. Excel filtering simulation
is_excel_month = month < '2026-02'
print(f"\nisExcelImportedMonth: {is_excel_month}")
if is_excel_month:
    filtered = [s for s in student_scores if str(s.get('notes','')).lower().startswith(('excel_total', 'excel_daily', 'excel_star'))]
    print(f"After Excel filter: {len(filtered)} scores")
else:
    filtered = student_scores
    print(f"No Excel filter applied: {len(filtered)} scores")

# 9. Compute total
total_pts = sum(int(s.get('points', 0) or 0) for s in filtered)
print(f"\nFinal computed total for {month}: {total_pts}")

# 10. Now do the same for an Excel month
month2 = '2024-10'
print(f"\n{'='*60}")
print(f"SIMULATING MONTH {month2}")
m2_scores = [s for s in data['scores'] if s.get('studentId') == student_id and (s.get('month') == month2 or (not s.get('month') and str(s.get('date',''))[:7] == month2))]
print(f"Total entries for student 1 in {month2}: {len(m2_scores)}")

excel_scores = [s for s in m2_scores if str(s.get('notes','')).lower().startswith(('excel_total', 'excel_daily', 'excel_star'))]
print(f"Excel entries: {len(excel_scores)}")
excel_total = sum(int(s.get('points',0) or 0) for s in excel_scores if str(s.get('notes','')).lower().startswith(('excel_total')))
excel_daily = sum(int(s.get('points',0) or 0) for s in excel_scores if str(s.get('notes','')).lower().startswith('excel_daily'))
print(f"Excel total entries points: {excel_total}")
print(f"Excel daily entries points: {excel_daily}")

# Check visibility
roster2 = data.get('month_students', {}).get(month2, [])
profiles2 = data.get('month_roster_profiles', {}).get(month2, [])
in_prof2 = any(p.get('studentId') == student_id for p in profiles2)
in_leg2 = 'EA24A01' in roster2
print(f"Visible in {month2}: inProfileRoster(by ID)={in_prof2}, inLegacyRoster(EA24A01)={in_leg2}")
